import uuid
from typing import List, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel
import asyncio
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Response, Request, BackgroundTasks, Form
from starlette.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, selectinload, Query
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from .models import Sequence, Accession, AllelePresence, get_session, DatabaseVersion, Program, \
    SequencePresence, program_source_association, \
    JobStatusResponse, \
    QueryRequest, PaginatedSequenceResponse, SequenceResponse, PaginatedSequenceRequest, \
    ColumnFilter, AccessionResponse, AccessionRequest, Source, SourceResponse, SourceCreate, \
    SupplementalJobStatusResponse, AccessionDetailResponse, VersionStatsResponse, ProgramResponse
from src.database import AsyncSessionLocal
from .service import get_all_batch_summaries, get_new_sequences_for_batch, get_total_unique_sequences, \
    generate_upset_plot, generate_line_chart, generate_line_chart_data
import pandas as pd
import io
import os
from datetime import datetime, timedelta
from sqlalchemy import func, text, or_, insert, and_, distinct
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.orcid_oauth import get_current_user
import logging

logging.basicConfig(level=logging.INFO)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Global cache for storing report data and last update timestamp
last_report_time = None
cached_report = None

jobs = {}
jobs_pav = {}
jobs_supplemental = {}


def is_safe_query(query: str) -> bool:
    query = query.strip().lower()
    if query.startswith("select"):
        return True
    return False


async def generate_report(request: Request, db=Depends(get_session)):
    # Background task function to generate the report

    try:
        total_unique_sequences = get_total_unique_sequences(db)
        new_sequences_this_batch = get_new_sequences_for_batch(db)
        batch_history = get_all_batch_summaries(db)
        line_chart_base64 = generate_line_chart(db)
        return templates.TemplateResponse("report_template.html", {
            "request": request,
            "total_unique_sequences": total_unique_sequences,
            "new_sequences_this_batch": new_sequences_this_batch,
            "batch_history": batch_history,
            "line_chart": line_chart_base64
        })
    finally:
        db.close()


from sqlalchemy.orm import Session


async def get_next_version_number(db: AsyncSession, species: str) -> int:
    stmt = select(func.max(UploadBatch.version)).where(UploadBatch.species == species)
    result = await db.execute(stmt)
    max_version = result.scalar()
    return (max_version or 0) + 1


import uuid


async def process_upload(file_data: bytes, job_id: str, species: str, program_id: int, source_name: str):
    async with AsyncSessionLocal() as db:
        try:
            # --- Create or update the Program-Source association ---
            # Retrieve the Program record
            stmt = select(Program).where(Program.id == program_id)
            result = await db.execute(stmt)
            program_obj = result.scalar_one_or_none()
            if not program_obj:
                logging.error("Program not found for ID %s", program_id)
                return

            # Look up the Source by name; if it doesn't exist, create it.
            stmt = select(Source).where(Source.name == source_name)
            result = await db.execute(stmt)
            source_obj = result.scalar_one_or_none()
            if not source_obj:
                source_obj = Source(name=source_name)
                db.add(source_obj)
                await db.flush()  # assign an ID to source_obj

            # Associate the source with the program if not already linked.
            stmt = select(Program).options(selectinload(Program.sources)).where(Program.id == program_id)
            result = await db.execute(stmt)
            program_obj = result.scalar_one_or_none()

            source_already_linked = any(source.id == source_obj.id for source in program_obj.sources)

            # If not already linked, add the association
            if not source_already_linked:
                program_obj.sources.append(source_obj)
                await db.flush()  # Ensure the association is persisted

            # --- Process the CSV upload as before ---
            df = pd.read_csv(io.StringIO(file_data.decode('utf-8')), header=0, low_memory=False)
            total_rows = len(df)
            logging.info(f"Total rows to process: {total_rows}")

            # Pre-fetch existing sequences for the given species using unique alleleIDs (assumed to be in the first column)
            unique_alleleids = df.iloc[:, 0].unique().tolist()
            stmt = select(Sequence.alleleid).where(
                Sequence.species == species,
                Sequence.alleleid.in_(unique_alleleids)
            )
            result = await db.execute(stmt)
            existing_sequences = {row.alleleid for row in result}
            logging.info(f"Found {len(existing_sequences)} existing sequences")

            # Create a new database version
            # Get the next version number for this species
            stmt = select(func.max(DatabaseVersion.version)).where(DatabaseVersion.species == species)
            result = await db.execute(stmt)
            current_version = result.scalar_one_or_none() or 0
            new_version = current_version + 1

            # Create the new database version record
            db_version = DatabaseVersion(
                version=new_version,
                program_id=program_id,
                species=species,
                description=f"Upload of {len(df)} sequences from {source_name}",
                changes_summary=f"Added {len(unique_alleleids) - len(existing_sequences)} new sequences"
            )
            db.add(db_version)
            await db.flush()

            # Prepare lists for bulk insertion
            new_sequences_data = []  # For new Sequence rows
            alleleids_processed = []  # For presence check
            new_sequences = set()  # Track new sequences in this job

            # Process each row using itertuples for fast iteration
            for i, row in enumerate(df.itertuples(index=False)):
                if i % 100 == 0:
                    logging.info(f"Processing row {i}/{total_rows}")
                # Assume first column is alleleid and third column is allelesequence.
                alleleid = getattr(row, df.columns[0])
                allelesequence = getattr(row, df.columns[2])

                # Check if the sequence already exists
                if alleleid in existing_sequences:
                    # Sequence already exists, no action needed for the sequence table
                    pass
                elif alleleid in new_sequences:
                    # We've already processed this new sequence in this batch
                    pass
                else:
                    new_sequences.add(alleleid)
                    new_sequences_data.append({
                        "alleleid": alleleid,
                        "allelesequence": allelesequence,
                        "species": species,
                        "info": None,
                        "associated_trait": None,
                        "version_added": new_version
                    })

                alleleids_processed.append(alleleid)

            # Bulk insert new Sequence rows (if any)
            if new_sequences_data:
                await db.execute(insert(Sequence), new_sequences_data)

            # Pre-fetch existing SequencePresence for all processed alleleids
            alleleid_set = set(alleleids_processed)
            stmt_presence = select(SequencePresence.alleleid).where(
                SequencePresence.program_id == program_id,
                SequencePresence.species == species,
                SequencePresence.alleleid.in_(alleleid_set)
            )
            result_presence = await db.execute(stmt_presence)
            existing_presence_alleleids = {row.alleleid for row in result_presence}

            # Prepare new SequencePresence rows for alleleids that do not have an entry yet
            new_presence_data = []
            for alleleid in alleleid_set:
                if alleleid not in existing_presence_alleleids:
                    new_presence_data.append({
                        "program_id": program_id,
                        "alleleid": alleleid,
                        "species": species,
                        "presence": True,
                        "version_added": new_version
                    })

            if new_presence_data:
                await db.execute(insert(SequencePresence), new_presence_data)

            # Final commit: persist all changes
            await db.commit()

            # Optionally, store CSV output for logging or download purposes
            output_stream = io.StringIO()
            df.to_csv(output_stream, index=False, header=False)
            output_stream.seek(0)
            jobs[job_id]['file'] = output_stream.getvalue()
            jobs[job_id]['status'] = 'Completed'
            jobs[job_id]['completion_time'] = datetime.utcnow()

            # Add summary information to job
            jobs[job_id]['version'] = new_version
            jobs[job_id]['new_sequences'] = len(new_sequences)
            jobs[job_id]['total_sequences'] = len(alleleids_processed)

        except Exception as e:
            await db.rollback()
            jobs[job_id]['status'] = 'Failed'
            logging.error(f"Error processing job {job_id}: {str(e)}")






async def add_accessions_pav(session: AsyncSession, accession_names: List[str]):
    """
    Adds new accessions to the database if they do not already exist.
    """
    # Remove duplicates
    accession_names = list(set(accession_names))

    # Fetch existing accessions
    existing = await session.execute(
        select(Accession).where(Accession.accession_name.in_(accession_names))
    )
    existing_accessions = existing.scalars().all()
    existing_names = {acc.accession_name for acc in existing_accessions}

    # Determine new accessions to add
    new_names = set(accession_names) - existing_names
    new_accessions = [Accession(accession_name=name) for name in new_names]

    if new_accessions:
        session.add_all(new_accessions)
        try:
            await session.commit()
            logging.info(f"Added new accessions: {[acc.accession_name for acc in new_accessions]}")
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=500, detail="Failed to add new accessions due to a database error.")


async def get_accession_map_pav(session: AsyncSession) -> Dict[str, int]:
    """
    Retrieves a mapping from accession_name to accession_id.
    """
    result = await session.execute(select(Accession))
    accessions = result.scalars().all()
    return {acc.accession_name: acc.accession_id for acc in accessions}


async def add_allele_accessions_pav(session: AsyncSession, allele_id: str, species: str, accession_map: Dict[str, int],
                                    accessions_presence: Dict[str, int]):
    """
    Adds or updates AlleleAccession records based on presence data.
    Only accessions with presence == 1 are stored.
    """
    allele_accessions = []
    for acc_name, presence in accessions_presence.items():
        if presence != 1:
            continue  # Skip accessions with presence == 0
        accession_id = accession_map.get(acc_name)
        if accession_id is None:
            logging.warning(f"Accession '{acc_name}' not found. Skipping.")
            continue
        allele_accessions.append(
            AllelePresence(
                alleleid=allele_id,
                species=species,  # Ensure species is set here
                accession_id=accession_id
            )
        )
    if allele_accessions:
        session.add_all(allele_accessions)
        try:
            await session.commit()
            logging.info(f"Added AllelePresence records for allele '{allele_id}' and species '{species}'")
        except IntegrityError:
            await session.rollback()
            logging.warning(
                f"IntegrityError: Possibly duplicate AllelePresence records for allele '{allele_id}' and species '{species}'")


async def process_pav_upload(file_data: bytes, job_id: str, species: str, program_id: int):
    async with AsyncSessionLocal() as db:
        try:
            # Read CSV file into a DataFrame
            df = pd.read_csv(io.StringIO(file_data.decode('utf-8')), header=0, low_memory=False)

            # Validate CSV structure: must have 'AlleleID' column and at least one accession column
            if 'AlleleID' not in df.columns:
                raise HTTPException(status_code=400, detail="CSV must contain 'AlleleID' as the first column.")
            accession_names = list(df.columns[1:])
            if not accession_names:
                raise HTTPException(status_code=400, detail="CSV must contain at least one accession column.")

            # Add any new accessions and retrieve the accession mapping
            await add_accessions_pav(db, accession_names)
            accession_map = await get_accession_map_pav(db)

            # Pre-fetch all allele IDs present in the CSV
            allele_ids = df['AlleleID'].dropna().unique().tolist()
            stmt = select(Sequence.alleleid).where(
                Sequence.alleleid.in_(allele_ids),
                Sequence.species == species
            )
            result = await db.execute(stmt)
            # Build a set of allele IDs that exist in the Sequence table
            existing_alleles = {row[0] for row in result.fetchall()}

            # Accumulate new AllelePresence records (for presence == 1)
            allele_presence_bulk = []

            # Process each row using itertuples for better performance
            for row in df.itertuples(index=False):
                alleleid = getattr(row, 'AlleleID')
                if alleleid not in existing_alleles:
                    logging.warning(f"AlleleID '{alleleid}' does not exist in the Sequence table. Skipping.")
                    continue

                # Build the presence mapping from the row (defaulting to 0 if missing)
                accessions_presence = {acc: getattr(row, acc, 0) for acc in accession_names}

                for acc_name, presence in accessions_presence.items():
                    if presence == 1:
                        accession_id = accession_map.get(acc_name)
                        if accession_id is None:
                            logging.warning(f"Accession '{acc_name}' not found. Skipping.")
                            continue
                        allele_presence_bulk.append({
                            "alleleid": alleleid,
                            "species": species,
                            "accession_id": accession_id
                        })

            # Bulk insert all AllelePresence records (if any)
            if allele_presence_bulk:
                await db.execute(insert(AllelePresence), allele_presence_bulk)

            # Final commit: all changes are persisted in one go
            await db.commit()

            # (Optional) Convert the DataFrame back to CSV for download/logging purposes
            output_stream = io.StringIO()
            df.to_csv(output_stream, index=False, header=False)
            output_stream.seek(0)
            jobs_pav[job_id]['file'] = output_stream.getvalue()
            jobs_pav[job_id]['status'] = 'Completed'
            jobs_pav[job_id]['completion_time'] = datetime.utcnow()
            logging.info(f"PAV Job {job_id} completed successfully.")
        except Exception as e:
            await db.rollback()
            jobs_pav[job_id]['status'] = 'Failed'
            jobs_pav[job_id]['error'] = str(e)
            logging.error(f"Error processing PAV job {job_id}: {str(e)}")


@router.post("/upload/preview")
async def preview_upload(
    file: UploadFile = File(...),
    species: str = Form(...),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """
    Preview the uploaded CSV to identify alleleIDs that already exist.
    This endpoint does not commit any data.
    """
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')), header=0, low_memory=False)
        unique_alleleids = df.iloc[:, 0].unique().tolist()
        total_count = len(unique_alleleids)  # Total alleleIDs in the file
        stmt = select(Sequence.alleleid).where(
            Sequence.species == species,
            Sequence.alleleid.in_(unique_alleleids)
        )
        result = await db.execute(stmt)
        existing_alleleids = [row[0] for row in result]
        duplicate_count = len(existing_alleleids)
        return {
            "duplicate_count": duplicate_count,
            "duplicates": existing_alleleids,
            "total_count": total_count  # Added so the modal can display "X out of Y..."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/upload/")
async def upload_microhaplotype_data(
        request: Request,
        file: UploadFile = File(...),
        species: str = Form(...),
        program_name: str = Form(...),
        source_name: str = Form(...),  # New form field for the source
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: AsyncSession = Depends(get_session)
):
    # Get or create the Program record based on program_name
    stmt = select(Program).filter(Program.name == program_name)
    result = await db.execute(stmt)
    existing_program = result.scalar_one_or_none()
    if not existing_program:
        new_program = Program(name=program_name)
        db.add(new_program)
        await db.commit()
        await db.refresh(new_program)
        program_obj = new_program
    else:
        program_obj = existing_program

    job_id = str(uuid4())
    contents = await file.read()
    jobs[job_id] = {
        'status': 'Processing',
        'submission_time': datetime.utcnow(),
        'file_name': file.filename
    }

    # Start background processing of the upload,
    # now passing source_name along with program_id.
    asyncio.create_task(
        process_upload(
            file_data=contents,
            job_id=job_id,
            species=species,
            program_id=program_obj.id,
            source_name=source_name
        )
    )
    return {"message": "Processing started. Check job status.", "job_id": job_id}



@router.post("/pav_upload/")
async def upload_pav_data(
        request: Request,
        file: UploadFile = File(...),
        species: str = Form(...),
        program_name: str = Form(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: AsyncSession = Depends(get_session)
):
    """
    Endpoint to upload PAV-formatted microhaplotype data.
    """
    # Validate file type
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Only CSV files are supported for PAV uploads.")

    # Get or create program based on the provided program_name
    result = await db.execute(select(Program).where(Program.name == program_name))
    existing_program = result.scalar_one_or_none()

    if not existing_program:
        new_program = Program(name=program_name)
        db.add(new_program)
        try:
            await db.commit()
            await db.refresh(new_program)
            program_id = new_program.id
            logging.info(f"Created new program: {program_name} with ID {program_id}")
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create new program due to a database error.")
    else:
        program_id = existing_program.id
        logging.info(f"Using existing program: {program_name} with ID {program_id}")

    job_id = str(uuid4())
    contents = await file.read()
    jobs_pav[job_id] = {
        'status': 'Processing',
        'submission_time': datetime.utcnow(),
        'file_name': file.filename
    }

    # Start the background task for PAV processing
    asyncio.create_task(process_pav_upload(file_data=contents, job_id=job_id,
                                           species=species, program_id=program_id))
    logging.info(f"Started PAV processing job {job_id} for file {file.filename}")
    return {"job_id": job_id, "message": "PAV processing started. Check job status."}


@router.get("/report_data")
async def get_report_data(species: str = 'all', db: AsyncSession = Depends(get_session)):
    try:
        total_unique_sequences = await get_total_unique_sequences(db, species)
        new_sequences_this_batch = await get_new_sequences_for_batch(db, species)
        batch_history = await get_all_batch_summaries(db, species)
        line_chart_data = await generate_line_chart_data(db, species)

        return {
            "total_unique_sequences": total_unique_sequences,
            "new_sequences_this_batch": new_sequences_this_batch,
            "batch_history": batch_history,
            "line_chart_data": line_chart_data,  # Now returns data instead of image
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/download/{job_id}")
async def download_processed_file(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job['status'] == 'Completed':
        return Response(content=job['file'], media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={job_id}.csv"})
    elif job['status'] == 'Processing':
        return {"status": "Still processing"}
    else:
        return {"status": "Failed to process the file"}


@router.get("/jobStatus", response_model=List[JobStatusResponse])
async def list_jobs():
    job_list = [{
        "job_id": job_id,
        "status": job['status'],
        "submission_time": job['submission_time'],
        "completion_time": job.get('completion_time'),
        "file_name": job.get('file_name')  # Include the filename
    } for job_id, job in jobs.items()]

    return job_list


@router.get("/pav_jobStatus", response_model=List[JobStatusResponse])
async def list_pav_jobs():
    """
    Endpoint to list all PAV upload jobs and their statuses.
    """
    job_list = [{
        "job_id": job_id,
        "status": job['status'],
        "submission_time": job['submission_time'],
        "completion_time": job.get('completion_time'),
        "file_name": job.get('file_name'),
        "error": job.get('error')
    } for job_id, job in jobs_pav.items()]

    return job_list


@router.get("/pav_alleles/{alleleid}/accessions")
async def get_pav_accessions_for_allele(alleleid: str, db: AsyncSession = Depends(get_session)):
    """
    Retrieve all accessions where a specific allele is present.
    """
    stmt = (
        select(Accession)
        .join(AllelePresence)
        .join(Sequence)
        .where(
            Sequence.alleleid == alleleid
            # AlleleAccession.presence == True
        )
    )
    result = await db.execute(stmt)
    accessions = result.scalars().all()
    return {"accessions": [acc.accession_name for acc in accessions]}


async def check_new_data_since_last_report(db: AsyncSession, last_report_time: datetime = None):
    # Query the latest batch entry time from the database
    result = await db.execute(select(func.max(UploadBatch.created_at)))
    latest_batch_time = result.scalar()
    return latest_batch_time > last_report_time if last_report_time and latest_batch_time else True


@router.post("/query")
async def execute_query(request: QueryRequest, db: AsyncSession = Depends(get_session)):
    query_str = request.query
    if not is_safe_query(query_str):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
    try:
        result = await db.execute(text(query_str))
        rows = result.fetchall()
        return {"result": [dict(row) for row in rows]}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/sequences", response_model=PaginatedSequenceResponse)
async def get_sequences(
        request: PaginatedSequenceRequest,
        db: AsyncSession = Depends(get_session)
):
    if request.page < 1:
        raise HTTPException(status_code=400, detail="Page number must be >= 1")

    query = select(Sequence)

    # Filter by species if provided
    if request.species:
        query = query.where(Sequence.species == request.species)

    # Apply global filter if provided
    if request.globalFilter:
        global_search = f"%{request.globalFilter}%"
        query = query.where(
            or_(
                Sequence.alleleid.ilike(global_search),
                Sequence.allelesequence.ilike(global_search),
                Sequence.species.ilike(global_search),
                Sequence.info.ilike(global_search),
                Sequence.associated_trait.ilike(global_search)
            )
        )

    # Apply column-specific filters
    if request.filters:
        for field, filter_obj in request.filters.items():
            if filter_obj.value:
                if field == 'alleleid':
                    query = query.where(Sequence.alleleid.ilike(f"%{filter_obj.value}%"))
                elif field == 'allelesequence':
                    query = query.where(Sequence.allelesequence.ilike(f"%{filter_obj.value}%"))
                elif field == 'info':
                    query = query.where(Sequence.info.ilike(f"%{filter_obj.value}%"))
                elif field == 'associated_trait':
                    query = query.where(Sequence.associated_trait.ilike(f"%{filter_obj.value}%"))

    # Calculate total records
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    # Apply pagination
    result = await db.execute(
        query.offset((request.page - 1) * request.size).limit(request.size)
    )
    sequences = result.scalars().all()

    # Prepare response
    return PaginatedSequenceResponse(
        total=total,
        items=[
            SequenceResponse(
                alleleid=seq.alleleid,
                species=seq.species,
                allelesequence=seq.allelesequence,
                info=seq.info,
                associated_trait=seq.associated_trait
            ) for seq in sequences
        ]
    )


@router.post("/alleleAccessions", response_model=List[AccessionDetailResponse])
async def get_accessions_by_allele(
    request: AccessionRequest,
    db: AsyncSession = Depends(get_session)
):
    if not request.alleleid:
        raise HTTPException(
            status_code=400,
            detail="List of alleleid cannot be empty."
        )

    # Build query that joins AllelePresence -> Accession -> Sequence -> SequencePresence -> Program
    # and left outer joins Program to Source via the association table.
    stmt = (
        select(
            AllelePresence.alleleid,
            Accession.accession_name,
            Program.name.label("program_name"),
            Source.name.label("source_name")
        )
        .join(Accession, AllelePresence.accession_id == Accession.accession_id)
        # Join Sequence using both alleleid and species (Sequence is unique per allele/species)
        .join(Sequence, and_(
            AllelePresence.alleleid == Sequence.alleleid,
            AllelePresence.species == Sequence.species
        ))
        # Join to SequencePresence to get program info
        .join(SequencePresence, and_(
            Sequence.alleleid == SequencePresence.alleleid,
            Sequence.species == SequencePresence.species
        ))
        .join(Program, SequencePresence.program_id == Program.id)
        # Left outer join to get Source info (if any)
        .outerjoin(program_source_association, Program.id == program_source_association.c.program_id)
        .outerjoin(Source, program_source_association.c.source_id == Source.id)
        .where(AllelePresence.alleleid.in_(request.alleleid))
    )

    result = await db.execute(stmt)
    records = result.fetchall()

    # Aggregate results by (alleleid, accession_name)
    mapping = {}
    for row in records:
        key = (row.alleleid, row.accession_name)
        if key not in mapping:
            mapping[key] = {
                "alleleid": row.alleleid,
                "accession": row.accession_name,
                "programs": set(),
                "sources": set()
            }
        if row.program_name:
            mapping[key]["programs"].add(row.program_name)
        if row.source_name:
            mapping[key]["sources"].add(row.source_name)

    # Log the details for each aggregated record
    for item in mapping.values():
        logging.info(
            "AlleleID: %s, Accession: %s, Programs: %s, Sources: %s",
            item["alleleid"],
            item["accession"],
            sorted(list(item["programs"])),
            sorted(list(item["sources"]))
        )

    # Prepare the response: flatten the sets into sorted lists
    response = []
    for item in mapping.values():
        response.append(AccessionDetailResponse(
            alleleid=item["alleleid"],
            accession=item["accession"],
            programs=sorted(list(item["programs"])),
            sources=sorted(list(item["sources"]))
        ))
    return response



@router.post("/alleleDetails", response_model=PaginatedSequenceResponse)
async def get_alleleDetails(
        request: PaginatedSequenceRequest,
        db: AsyncSession = Depends(get_session)
):
    if request.page < 1:
        raise HTTPException(status_code=400, detail="Page number must be >= 1")

    query = select(Sequence)

    # Filter by species if provided
    if request.species:
        query = query.where(Sequence.species == request.species)

    # Apply global filter if provided
    if request.globalFilter:
        global_search = f"%{request.globalFilter}%"
        query = query.where(
            or_(
                Sequence.alleleid.ilike(global_search),
                Sequence.allelesequence.ilike(global_search),
                Sequence.species.ilike(global_search),
                Sequence.info.ilike(global_search),  # Include new field
                Sequence.associated_trait.ilike(global_search)  # Include new field
            )
        )

    # Apply column-specific filters
    if request.filters:
        for field, filter_obj in request.filters.items():
            if filter_obj.value:
                if field == 'alleleid':
                    query = query.where(Sequence.alleleid.ilike(f"%{filter_obj.value}%"))
                elif field == 'allelesequence':
                    query = query.where(Sequence.allelesequence.ilike(f"%{filter_obj.value}%"))
                elif field == 'info':  # New filter
                    query = query.where(Sequence.info.ilike(f"%{filter_obj.value}%"))
                elif field == 'associated_trait':  # New filter
                    query = query.where(Sequence.associated_trait.ilike(f"%{filter_obj.value}%"))
                # Add more fields here as needed

    # Calculate total records
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    # Apply pagination
    result = await db.execute(
        query.offset((request.page - 1) * request.size).limit(request.size)
    )
    sequences = result.scalars().all()

    # Prepare response
    return PaginatedSequenceResponse(
        total=total,
        items=[
            SequenceResponse(
                alleleid=seq.alleleid,
                allelesequence=seq.allelesequence,
                species=seq.species,
                info=seq.info,  # Include new field
                associated_trait=seq.associated_trait  # Include new field
            ) for seq in sequences
        ]
    )


@router.post("/sequences/alignment")
async def get_sequences_for_alignment(filter: str = "", filter_field: str = "", species: str = "",
                                      db: AsyncSession = Depends(get_session)) -> List[str]:
    query = select(Sequence).where(Sequence.species == species)

    if filter and filter_field:
        if filter_field == "alleleid":
            query = query.where(Sequence.alleleid.ilike(f"%{filter}%"))
        elif filter_field == "allelesequence":
            query = query.where(Sequence.allelesequence.ilike(f"%{filter}%"))

    result = await db.execute(query)
    sequences = result.scalars().all()

    sequence_data = [sequence.allelesequence for sequence in sequences]
    return sequence_data


@router.get("/programs/list")
async def get_programs(db: AsyncSession = Depends(get_session)):
    programs = await db.execute(select(Program))
    program_list = programs.scalars().all()
    return {"programs": [{"id": program.id, "name": program.name} for program in program_list]}


class ProgramCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


@router.get("/programs/by_species/{species}")
async def get_programs_by_species(species: str, db: AsyncSession = Depends(get_session)):
    """
    Get programs that have database versions for the specified species.
    """
    try:
        # Find programs that have database versions for this species
        stmt = (
            select(Program)
            .join(DatabaseVersion, Program.id == DatabaseVersion.program_id)
            .where(DatabaseVersion.species == species)
            .distinct()
            .order_by(Program.name)
        )

        result = await db.execute(stmt)
        programs = result.scalars().all()

        return {"programs": [{"id": program.id, "name": program.name} for program in programs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving programs: {str(e)}")

@router.post("/programs/create")
async def create_program(request: ProgramCreateRequest, db: AsyncSession = Depends(get_session)):
    # Check if a program with the same name already exists
    result = await db.execute(select(Program).filter(Program.name == request.name))
    existing_program = result.scalar_one_or_none()

    if existing_program:
        raise HTTPException(status_code=400, detail="Program with this name already exists.")

    # Create a new program instance
    new_program = Program(name=request.name, description=request.description)
    db.add(new_program)

    try:
        await db.commit()
        await db.refresh(new_program)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create program due to a database error.")

    return {"program": {"id": new_program.id, "name": new_program.name, "description": new_program.description}}


@router.get("/sources/list", response_model=List[SourceResponse])
async def list_sources(db: AsyncSession = Depends(get_session)):
    sources = await db.execute(select(Source))
    source_list = sources.scalars().all()
    return source_list


@router.get("/sources/by_program/{program_id}")
async def get_sources_by_program(program_id: int, db: AsyncSession = Depends(get_session)):
    """
    Get sources associated with a specific program.
    """
    try:
        # Use the association table to find sources linked to this program
        stmt = (
            select(Source)
            .join(program_source_association, Source.id == program_source_association.c.source_id)
            .where(program_source_association.c.program_id == program_id)
            .order_by(Source.name)
        )

        result = await db.execute(stmt)
        sources = result.scalars().all()

        return [{"id": source.id, "name": source.name, "value": source.name} for source in sources]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sources: {str(e)}")

@router.post("/sources/create", response_model=SourceResponse)
async def create_source(source: SourceCreate, db: AsyncSession = Depends(get_session)):
    # Check if the source already exists
    existing_source = await db.execute(select(Source).where(Source.name == source.name))
    if existing_source.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Source with this name already exists.")

    new_source = Source(name=source.name, description=source.description)
    db.add(new_source)
    try:
        await db.commit()
        await db.refresh(new_source)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create source due to a database error.")

    return new_source


@router.post("/supplemental_upload/")
async def upload_supplemental_data(
        request: Request,
        file: UploadFile = File(...),
        species: str = Form(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: AsyncSession = Depends(get_session)
):
    """
    Endpoint to upload supplemental data CSV.
    """
    # Validate file type
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Only CSV files are supported for supplemental uploads.")

    # Generate a unique job ID
    job_id = str(uuid.uuid4())

    # Read file contents
    contents = await file.read()

    # Initialize job status
    jobs_supplemental[job_id] = {
        'status': 'Processing',
        'submission_time': datetime.utcnow(),
        'file_name': file.filename,
        'missing_allele_ids': []
    }

    # Start background task
    asyncio.create_task(process_supplemental_upload(
        file_data=contents,
        job_id=job_id,
        species=species
    ))

    return {"job_id": job_id, "message": "Supplemental processing started. Check job status."}


async def process_supplemental_upload(file_data: bytes, job_id: str, species: str):
    """
    Background task to process supplemental upload CSV.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Read the CSV file into a DataFrame
            df = pd.read_csv(io.StringIO(file_data.decode('utf-8')), header=0, low_memory=False)

            # Validate CSV columns
            required_columns = {"AlleleID", "INFO", "Associated Trait"}
            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                raise HTTPException(status_code=400, detail=f"Missing columns: {', '.join(missing)}")

            missing_allele_ids = []
            for index, row in df.iterrows():
                alleleid = row['AlleleID']
                info = row['INFO']
                associated_trait = row['Associated Trait']

                if not alleleid:
                    # Optionally, log or skip rows with missing AlleleID
                    logging.warning(f"Row {index + 1} skipped: Missing AlleleID.")
                    continue

                # Handle NaN values by converting them to None
                info = row['INFO'] if pd.notna(row['INFO']) else None
                associated_trait = row['Associated Trait'] if pd.notna(row['Associated Trait']) else None

                # Check if AlleleID exists in the Sequence table for the species
                stmt = select(Sequence).where(
                    Sequence.alleleid == alleleid,
                    Sequence.species == species
                )
                result = await db.execute(stmt)
                sequence_entry = result.scalar_one_or_none()

                if sequence_entry:
                    # Update INFO and Associated Trait
                    sequence_entry.info = info
                    sequence_entry.associated_trait = associated_trait
                    db.add(sequence_entry)
                else:
                    # Collect missing AlleleIDs
                    missing_allele_ids.append(alleleid)

            # Commit the updates
            await db.commit()

            # Update job status
            jobs_supplemental[job_id]['status'] = 'Completed'
            jobs_supplemental[job_id]['completion_time'] = datetime.utcnow()
            jobs_supplemental[job_id]['missing_allele_ids'] = missing_allele_ids

            if missing_allele_ids:
                logging.info(f"Supplemental job {job_id} completed with missing AlleleIDs: {missing_allele_ids}")
            else:
                logging.info(f"Supplemental job {job_id} completed successfully with no missing AlleleIDs.")
        except HTTPException as he:
            await db.rollback()
            jobs_supplemental[job_id]['status'] = 'Failed'
            jobs_supplemental[job_id]['error'] = he.detail
            logging.error(f"Error processing supplemental job {job_id}: {he.detail}")
        except Exception as e:
            await db.rollback()
            jobs_supplemental[job_id]['status'] = 'Failed'
            jobs_supplemental[job_id]['error'] = str(e)
            logging.error(f"Error processing supplemental job {job_id}: {str(e)}")

@router.get("/supplemental_jobStatus", response_model=List[SupplementalJobStatusResponse])
async def list_supplemental_jobs():
    """
    Endpoint to list all supplemental upload jobs and their statuses, including missing AlleleIDs.
    """
    job_list = [{
        "job_id": job_id,
        "status": job['status'],
        "submission_time": job['submission_time'],
        "completion_time": job.get('completion_time'),
        "file_name": job.get('file_name'),
        "missing_allele_ids": job.get('missing_allele_ids'),
        "error": job.get('error')
    } for job_id, job in jobs_supplemental.items()]

    return job_list


@router.get("/visualizations/histogram")
async def get_histogram_data(
        species: str,
        chromosome: str,
        program_id: Optional[int] = None,
        db: AsyncSession = Depends(get_session)
):
    """
    Returns counts of alleles grouped by locus for a given species, chromosome, and optionally program_id.
    The alleleID format is assumed to be 'chromosome.locus|uniqueID'.
    """
    print(f"Received request with species: {species}, chromosome: {chromosome}, program_id: {program_id}")
    try:
        # Base query parameters
        query_params = {'species': species, 'chromosome': chromosome}

        # Construct the base query
        base_query = """
            SELECT 
                split_part(s.alleleid, '.', 1) AS chromosome,
                split_part(split_part(s.alleleid, '.', 2), '|', 1) AS locus,
                COUNT(*) AS allele_count
            FROM sequence_table s
        """

        # If program_id is provided, join with sequence_presence to filter by program
        if program_id is not None:
            base_query += """
            JOIN sequence_presence sp ON 
                s.alleleid = sp.alleleid AND 
                s.species = sp.species
            WHERE s.species = :species
              AND split_part(s.alleleid, '.', 1) = :chromosome
              AND sp.program_id = :program_id
            """
            query_params['program_id'] = program_id
        else:
            # Simple query without program filtering
            base_query += """
            WHERE s.species = :species
              AND split_part(s.alleleid, '.', 1) = :chromosome
            """

        # Complete the query with group by and order by clauses
        complete_query = base_query + """
            GROUP BY 
                split_part(s.alleleid, '.', 1),
                split_part(split_part(s.alleleid, '.', 2), '|', 1)
            ORDER BY locus;
        """

        # Execute the query with parameters
        query = text(complete_query)
        print("Executing query:")
        print(query)
        print("With parameters:", query_params)

        result = await db.execute(query, query_params)
        rows = result.fetchall()
        print(f"Query returned {len(rows)} rows")

        # Format the data for the frontend
        data = [
            {"chromosome": row.chromosome, "locus": row.locus, "allele_count": row.allele_count}
            for row in rows
        ]

        return {"data": data}
    except Exception as e:
        print("Error retrieving histogram data:", e)
        import traceback
        error_details = traceback.format_exc()
        print(f"Error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error retrieving histogram data: {e}")


@router.get("/visualizations/comparative")
async def get_comparative_data(
        species: str,
        chromosome: str,
        program_id: int,
        db: AsyncSession = Depends(get_session)
):
    """
    Returns comparative data between a program's alleles and the entire database.
    For each locus, returns:
    1. Total allele count in the database
    2. Allele count in the specified program
    3. List of alleles present in the database but missing from the program
    """
    try:
        # Query parameters
        query_params = {'species': species, 'chromosome': chromosome, 'program_id': program_id}

        # 1. Get total allele counts by locus for the entire database
        total_query = """
            SELECT 
                split_part(s.alleleid, '.', 1) AS chromosome,
                split_part(split_part(s.alleleid, '.', 2), '|', 1) AS locus,
                COUNT(*) AS total_count,
                array_agg(s.alleleid) AS allele_ids
            FROM sequence_table s
            WHERE s.species = :species
              AND split_part(s.alleleid, '.', 1) = :chromosome
            GROUP BY 
                split_part(s.alleleid, '.', 1),
                split_part(split_part(s.alleleid, '.', 2), '|', 1)
        """
        
        # 2. Get allele counts by locus for the specified program
        program_query = """
            SELECT 
                split_part(s.alleleid, '.', 1) AS chromosome,
                split_part(split_part(s.alleleid, '.', 2), '|', 1) AS locus,
                COUNT(*) AS program_count,
                array_agg(s.alleleid) AS program_allele_ids
            FROM sequence_table s
            JOIN sequence_presence sp ON 
                s.alleleid = sp.alleleid AND 
                s.species = sp.species
            WHERE s.species = :species
              AND split_part(s.alleleid, '.', 1) = :chromosome
              AND sp.program_id = :program_id
            GROUP BY 
                split_part(s.alleleid, '.', 1),
                split_part(split_part(s.alleleid, '.', 2), '|', 1)
        """

        # Execute the queries
        total_result = await db.execute(text(total_query), query_params)
        program_result = await db.execute(text(program_query), query_params)
        
        # Process results
        total_data = {row.locus: {"total_count": row.total_count, "allele_ids": row.allele_ids} 
                     for row in total_result}
        program_data = {row.locus: {"program_count": row.program_count, "program_allele_ids": row.program_allele_ids} 
                       for row in program_result}
        
        # Combine the results
        combined_data = []
        for locus, total_info in total_data.items():
            program_info = program_data.get(locus, {"program_count": 0, "program_allele_ids": []})
            
            # Calculate missing alleles
            total_allele_set = set(total_info["allele_ids"])
            program_allele_set = set(program_info.get("program_allele_ids", []))
            missing_alleles = list(total_allele_set - program_allele_set)
            
            combined_data.append({
                "locus": locus,
                "total_count": total_info["total_count"],
                "program_count": program_info.get("program_count", 0),
                "difference": total_info["total_count"] - program_info.get("program_count", 0),
                "missing_alleles": missing_alleles,
                "missing_count": len(missing_alleles)
            })
        
        # Sort by locus
        combined_data.sort(key=lambda x: x["locus"])
        
        return {"data": combined_data}
    except Exception as e:
        logging.error(f"Error retrieving comparative data: {e}")
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error retrieving comparative data: {e}")


@router.get("/visualizations/chromosomes")
async def get_chromosomes_for_species(
        species: str,
        db: AsyncSession = Depends(get_session)
):
    """
    Returns available chromosomes for a given species by parsing AlleleIDs.
    The alleleID format is assumed to be 'chromosome.locus|uniqueID'.
    """
    try:
        # Use PostgreSQL's split_part function to extract the chromosome part from alleleID
        query = text("""
            SELECT DISTINCT split_part(alleleid, '.', 1) AS chromosome
            FROM sequence_table
            WHERE species = :species
            ORDER BY chromosome;
        """)

        result = await db.execute(query, {'species': species})
        rows = result.fetchall()

        # Extract chromosome values from the result
        chromosomes = [row.chromosome for row in rows]

        return {"chromosomes": chromosomes}
    except Exception as e:
        logging.error(f"Error retrieving chromosomes for species {species}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving chromosomes: {e}")


@router.get("/allele-count/{species}", response_model=List[VersionStatsResponse])
async def get_allele_counts_by_version(
    species: str,
    program_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Get the count of unique alleleIDs for each database version of the specified species.
    Optionally filter by program ID.
    """
    try:
        # Query to get the total allele count for each version
        query = (
            select(
                DatabaseVersion.version,
                DatabaseVersion.species,
                DatabaseVersion.created_at,
                DatabaseVersion.description,
                func.count(distinct(Sequence.alleleid)).label("total_alleles"),
                Program.name.label("program_name")
            )
            .join(Sequence, Sequence.version_added <= DatabaseVersion.version)
            .join(Program, DatabaseVersion.program_id == Program.id)
            .where(
                DatabaseVersion.species == species,
                Sequence.species == species
            )
            .group_by(
                DatabaseVersion.version,
                DatabaseVersion.species,
                DatabaseVersion.created_at,
                DatabaseVersion.description,
                Program.name
            )
            .order_by(DatabaseVersion.version)
        )

        if program_id is not None:
            query = query.where(DatabaseVersion.program_id == program_id)

        result = await session.execute(query)
        versions_with_total = result.all()

        # Now get new allele counts for each version
        new_alleles_query = (
            select(
                DatabaseVersion.version,
                func.count(distinct(Sequence.alleleid)).label("new_alleles")
            )
            .join(Sequence, Sequence.version_added == DatabaseVersion.version)
            .where(
                DatabaseVersion.species == species,
                Sequence.species == species
            )
            .group_by(DatabaseVersion.version)
        )

        if program_id is not None:
            new_alleles_query = new_alleles_query.where(DatabaseVersion.program_id == program_id)

        new_alleles_result = await session.execute(new_alleles_query)
        new_alleles_by_version = {row.version: row.new_alleles for row in new_alleles_result}

        # Combine the results
        response_data = []
        for row in versions_with_total:
            response_data.append(
                VersionStatsResponse(
                    version=row.version,
                    species=row.species,
                    created_at=row.created_at,
                    total_alleles=row.total_alleles,
                    new_alleles=new_alleles_by_version.get(row.version, 0),
                    program_name=row.program_name,
                    description=row.description
                )
            )

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving version statistics: {str(e)}")


@router.get("/programs/", response_model=List[ProgramResponse])
async def get_programs(session: AsyncSession = Depends(get_session)):
    """
    Get a list of all programs for the dropdown selector.
    """
    try:
        query = select(Program).order_by(Program.name)
        result = await session.execute(query)
        programs = result.scalars().all()

        if not programs:
            return []

        return programs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving programs: {str(e)}")


@router.get("/database_version/{species}", response_model=dict)
async def get_latest_database_version(species: str, db: AsyncSession = Depends(get_session)):
    """
    Get the latest database version for a given species.
    """
    try:
        # Use a simpler query approach with subquery to find the max version
        subquery = select(func.max(DatabaseVersion.version)).where(
            DatabaseVersion.species == species.lower()).scalar_subquery()

        # Then fetch the complete row for that version
        query = select(DatabaseVersion).where(
            (DatabaseVersion.species == species.lower()) &
            (DatabaseVersion.version == subquery)
        )

        result = await db.execute(query)
        version_data = result.scalars().first()

        if not version_data:
            return {"version": None, "message": f"No database found for species: {species}"}

        # Return data directly from the model
        return {
            "version": version_data.version,
            "created_at": version_data.created_at.isoformat() if version_data.created_at else None,
            "description": version_data.description,
            "species": species,
            "program": version_data.program_id  # This will include the program ID
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error fetching database version for {species}: {str(e)}\n{error_details}")

        raise HTTPException(
            status_code=500,
            detail=f"Error fetching database version: {str(e)}"
        )
