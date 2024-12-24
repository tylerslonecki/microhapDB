import uuid
from typing import List, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel
import asyncio
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Response, Request, BackgroundTasks, Form
from starlette.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from .models import Sequence, Accession, AllelePresence, get_session, UploadBatch, SequenceLog, Program, \
    SequencePresence, \
    JobStatusResponse, \
    QueryRequest, PaginatedSequenceResponse, SequenceResponse, PaginatedSequenceRequest, \
    AsyncSessionLocal, ColumnFilter, AccessionResponse, AccessionRequest, Source, SourceResponse, SourceCreate
from .service import get_all_batch_summaries, get_new_sequences_for_batch, get_total_unique_sequences, \
    generate_upset_plot, generate_line_chart, generate_line_chart_data
import pandas as pd
import io
import os
from datetime import datetime, timedelta
from sqlalchemy import func, text, or_
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
jobs_eav = {}


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


async def process_upload(file_data, job_id, species, program_id):
    async with AsyncSessionLocal() as db:
        try:
            df = pd.read_csv(io.StringIO(file_data.decode('utf-8')), header=0, low_memory=False)
            version = await get_next_version_number(db, species)
            batch = UploadBatch(program_id=program_id, species=species, version=version)
            db.add(batch)
            await db.flush()  # Flush to get batch.id

            # Remove code that ensures 'hapid' column and assigns it to df
            # No DataFrame modifications related to hapid here

            for index in range(len(df)):
                alleleid = df.iloc[index, 0]
                allelesequence = df.iloc[index, 2]

                # Check for existing sequence by alleleid
                stmt = select(Sequence).where(
                    Sequence.alleleid == alleleid,
                    Sequence.species == species
                )
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()

                try:
                    if not existing:
                        new_hap = Sequence(
                            alleleid=alleleid,
                            allelesequence=allelesequence,
                            species=species
                        )
                        db.add(new_hap)
                        await db.flush()  # Flush to get hapid
                        hapid = new_hap.hapid
                        was_new = True
                    else:
                        hapid = existing.hapid
                        was_new = False
                except IntegrityError:
                    await db.rollback()
                    # If inserted by another transaction, fetch again
                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()
                    if existing:
                        hapid = existing.hapid
                        was_new = False
                    else:
                        raise ValueError(
                            f"Failed to retrieve or create Sequence for alleleid: {alleleid}, species: {species}")

                # Log the sequence
                log_entry = SequenceLog(
                    hapid=hapid,
                    batch_id=batch.id,
                    was_new=was_new,
                    species=species,
                    alleleid=alleleid,
                    allelesequence=allelesequence
                )
                db.add(log_entry)

                # Update SequencePresence
                presence_stmt = select(SequencePresence).where(
                    SequencePresence.program_id == program_id,
                    SequencePresence.hapid == hapid,
                    SequencePresence.species == species
                )
                result = await db.execute(presence_stmt)
                presence_entry = result.scalar_one_or_none()

                if not presence_entry:
                    # Add new presence record
                    presence_entry = SequencePresence(
                        program_id=program_id,
                        hapid=hapid,
                        presence=True,
                        species=species
                    )
                    db.add(presence_entry)

            # Commit transaction after all operations
            await db.commit()

            # Convert DataFrame back to CSV (no hapid column added)
            output_stream = io.StringIO()
            df.to_csv(output_stream, index=False, header=False)
            output_stream.seek(0)
            output_csv = output_stream.getvalue().encode('utf-8')
            jobs[job_id]['file'] = output_stream.getvalue()
            jobs[job_id]['status'] = 'Completed'
            jobs[job_id]['completion_time'] = datetime.utcnow()
        except Exception as e:
            await db.rollback()
            jobs[job_id]['status'] = 'Failed'
            print(f"Error processing job {job_id}: {str(e)}")


# Helper Functions for EAV Model

# Helper Functions for EAV Model

async def add_accessions_eav(session: AsyncSession, accession_names: List[str]):
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


async def get_accession_map_eav(session: AsyncSession) -> Dict[str, int]:
    """
    Retrieves a mapping from accession_name to accession_id.
    """
    result = await session.execute(select(Accession))
    accessions = result.scalars().all()
    return {acc.accession_name: acc.accession_id for acc in accessions}


async def add_allele_accessions_eav(session: AsyncSession, allele_id: str, species: str, accession_map: Dict[str, int],
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


async def process_eav_upload(file_data: bytes, job_id: str, species: str, program_id: int):
    async with AsyncSessionLocal() as db:
        logging.info("Here-3")
        try:
            logging.info("Here-2")
            # Read the CSV file into a DataFrame
            df = pd.read_csv(io.StringIO(file_data.decode('utf-8')), header=0, low_memory=False)
            logging.info("Here-1.5")
            # Validate CSV Structure
            if 'AlleleID' not in df.columns:
                raise HTTPException(status_code=400, detail="CSV must contain 'AlleleID' as the first column.")
            logging.info("Here-1.25")
            # Extract accession names from the header (excluding the first column 'AlleleID')
            accession_names = list(df.columns[1:])
            logging.info("Here-1")
            if not accession_names:
                raise HTTPException(status_code=400, detail="CSV must contain at least one accession column.")

            # Add accessions to the database
            await add_accessions_eav(db, accession_names)

            # Retrieve accession_id mapping
            accession_map = await get_accession_map_eav(db)
            logging.info("Here0")
            # Iterate over each row in the DataFrame
            for _, row in df.iterrows():
                alleleid = row['AlleleID']
                # Assuming 'AlleleSequence' is in a specific column, e.g., 'AlleleSequence'
                # Since we're not creating or modifying sequences, we ignore 'AlleleSequence' here
                # If needed, you can validate or use it for other purposes

                if not alleleid:
                    logging.warning("Missing 'AlleleID' value in a row. Skipping.")
                    continue  # Skip rows without an allele identifier
                logging.info("Here1")
                # Check if the allele exists in the Sequence table
                stmt = select(Sequence).where(
                    Sequence.alleleid == alleleid,
                    Sequence.species == species
                )
                logging.info("Here2")
                result = await db.execute(stmt)
                existing_sequence = result.scalar_one_or_none()

                if not existing_sequence:
                    logging.warning(f"AlleleID '{alleleid}' does not exist in the Sequence table. Skipping.")
                    continue  # Skip alleles that do not exist

                # Prepare allele_accessions data (presence/absence)
                accessions_presence = {acc: row.get(acc, 0) for acc in accession_names}

                # Add or update AlleleAccession records
                await add_allele_accessions_eav(db, alleleid, species, accession_map, accessions_presence)

            # Commit transaction after all operations
            await db.commit()

            # Convert DataFrame back to CSV (no hapid column added)
            output_stream = io.StringIO()
            df.to_csv(output_stream, index=False, header=False)
            output_stream.seek(0)
            output_csv = output_stream.getvalue().encode('utf-8')
            jobs_eav[job_id]['file'] = output_stream.getvalue()
            jobs_eav[job_id]['status'] = 'Completed'
            jobs_eav[job_id]['completion_time'] = datetime.utcnow()
            logging.info(f"EAV Job {job_id} completed successfully.")
        except Exception as e:
            await db.rollback()
            jobs_eav[job_id]['status'] = 'Failed'
            jobs_eav[job_id]['error'] = str(e)
            logging.error(f"Error processing EAV job {job_id}: {str(e)}")


@router.post("/upload/")
async def upload_microhaplotype_data(
        request: Request,
        file: UploadFile = File(...),
        species: str = Form(...),
        program_name: str = Form(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: AsyncSession = Depends(get_session)
):
    # Get or create program based on the provided program_name
    result = await db.execute(select(Program).filter(Program.name == program_name))
    existing_program = result.scalar_one_or_none()

    if not existing_program:
        new_program = Program(name=program_name)
        db.add(new_program)
        await db.commit()
        await db.refresh(new_program)
        program_id = new_program.id
    else:
        program_id = existing_program.id

    job_id = str(uuid4())
    contents = await file.read()
    jobs[job_id] = {
        'status': 'Processing',
        'submission_time': datetime.utcnow(),
        'file_name': file.filename
    }

    # Add program_id to the background task
    asyncio.create_task(process_upload(file_data=contents, job_id=job_id,
                                       species=species, program_id=program_id))
    return {"message": "Processing started. Check job status."}


@router.post("/eav_upload/")
async def upload_eav_data(
        request: Request,
        file: UploadFile = File(...),
        species: str = Form(...),
        program_name: str = Form(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: AsyncSession = Depends(get_session)
):
    """
    Endpoint to upload EAV-formatted microhaplotype data.
    """
    # Validate file type
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Only CSV files are supported for EAV uploads.")

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
    jobs_eav[job_id] = {
        'status': 'Processing',
        'submission_time': datetime.utcnow(),
        'file_name': file.filename
    }

    # Start the background task for EAV processing
    asyncio.create_task(process_eav_upload(file_data=contents, job_id=job_id,
                                           species=species, program_id=program_id))
    logging.info(f"Started EAV processing job {job_id} for file {file.filename}")
    return {"job_id": job_id, "message": "EAV processing started. Check job status."}


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


@router.get("/eav_jobStatus", response_model=List[JobStatusResponse])
async def list_eav_jobs():
    """
    Endpoint to list all EAV upload jobs and their statuses.
    """
    job_list = [{
        "job_id": job_id,
        "status": job['status'],
        "submission_time": job['submission_time'],
        "completion_time": job.get('completion_time'),
        "file_name": job.get('file_name'),
        "error": job.get('error')
    } for job_id, job in jobs_eav.items()]

    return job_list


@router.get("/eav_alleles/{alleleid}/accessions")
async def get_eav_accessions_for_allele(alleleid: str, db: AsyncSession = Depends(get_session)):
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
                Sequence.hapid.ilike(global_search),
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
                if field == 'hapid':
                    try:
                        uuid.UUID(filter_obj.value)
                        query = query.where(Sequence.hapid == filter_obj.value)
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid UUID format for hapid")
                elif field == 'alleleid':
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
                hapid=str(seq.hapid),
                alleleid=seq.alleleid,
                allelesequence=seq.allelesequence,
                species=seq.species,
                info=seq.info,  # Include new field
                associated_trait=seq.associated_trait  # Include new field
            ) for seq in sequences
        ]
    )


@router.post("/alleleAccessions", response_model=List[AccessionResponse])
async def get_accessions_by_allele(
        request: AccessionRequest,
        db: AsyncSession = Depends(get_session)
):
    if not request.alleleid:
        raise HTTPException(
            status_code=400,
            detail="List of alleleid cannot be empty."
        )

    # Query AllelePresence joined with Accession
    stmt = (
        select(AllelePresence.alleleid, Accession.accession_name)
        .join(Accession, AllelePresence.accession_id == Accession.accession_id)
        .where(AllelePresence.alleleid.in_(request.alleleid))
    )

    result = await db.execute(stmt)
    records = result.fetchall()

    # Organize accessions by alleleid
    allele_to_accessions: Dict[str, List[str]] = {}
    for alleleid, accession_name in records:
        if alleleid not in allele_to_accessions:
            allele_to_accessions[alleleid] = []
        allele_to_accessions[alleleid].append(accession_name)

    # Prepare response
    response = [
        AccessionResponse(
            alleleid=alleleid,
            accessions=accessions
        )
        for alleleid, accessions in allele_to_accessions.items()
    ]

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
                Sequence.hapid.ilike(global_search),
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
                if field == 'hapid':
                    try:
                        uuid.UUID(filter_obj.value)
                        query = query.where(Sequence.hapid == filter_obj.value)
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid UUID format for hapid")
                elif field == 'alleleid':
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
                hapid=str(seq.hapid),
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
        if filter_field == "hapid":
            query = query.where(Sequence.hapid.ilike(f"%{filter}%"))
        elif filter_field == "alleleid":
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
