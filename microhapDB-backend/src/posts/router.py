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
from sqlalchemy.dialects.postgresql import insert as pg_insert
from .models import Sequence, Accession, AllelePresence, get_session, DatabaseVersion, Program, \
    SequencePresence, program_project_association, \
    JobStatusResponse, \
    QueryRequest, PaginatedSequenceResponse, SequenceResponse, PaginatedSequenceRequest, \
    ColumnFilter, AccessionResponse, AccessionRequest, Project, ProjectResponse, ProjectCreate, \
    SupplementalJobStatusResponse, AccessionDetailResponse, VersionStatsResponse, ProgramResponse
from src.database import AsyncSessionLocal
from .service import get_all_batch_summaries, get_new_sequences_for_batch, get_total_unique_sequences, \
    generate_upset_plot, generate_line_chart, generate_line_chart_data
from src.auth.dependencies import get_current_user
from src.models import User, Collaboration, UserRoleEnum, FileUpload
from .rbac import require_admin_access, require_private_access, require_collaborator_access, check_data_access, get_accessible_data
import pandas as pd
import io
import os
from datetime import datetime, timedelta
from sqlalchemy import func, text, or_, insert, and_, distinct
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
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
    stmt = select(func.max(DatabaseVersion.version)).where(DatabaseVersion.species == species)
    result = await db.execute(stmt)
    max_version = result.scalar()
    return (max_version or 0) + 1


import uuid


async def process_upload(file_data: bytes, job_id: str, species: str, program_id: int, project_name: str, file_name: str = None, file_size: int = None, uploaded_by: int = None):
    async with AsyncSessionLocal() as db:
        try:
            # --- Create or update the Program-Project association ---
            # Retrieve the Program record with its projects
            stmt = select(Program).options(selectinload(Program.projects)).where(Program.id == program_id)
            result = await db.execute(stmt)
            program_obj = result.scalar_one_or_none()
            if not program_obj:
                logging.error("Program not found for ID %s", program_id)
                return

            # Look for a project with the given name that's already associated with this program
            project_obj = next((project for project in program_obj.projects if project.name == project_name), None)
            
            # If no matching project is found for this program, create a new one
            if not project_obj:
                project_obj = Project(name=project_name)
                db.add(project_obj)
                await db.flush()  # assign an ID to project_obj
                
                # Associate the new project with the program
                program_obj.projects.append(project_obj)
                await db.flush()  # Ensure the association is persisted
                logging.info(f"Created new project '{project_name}' and associated it with program ID {program_id}")
            else:
                logging.info(f"Using existing project '{project_name}' already associated with program ID {program_id}")

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
            # Get the next species-specific version number
            stmt = select(func.max(DatabaseVersion.version)).where(DatabaseVersion.species == species)
            result = await db.execute(stmt)
            current_version = result.scalar_one_or_none() or 0
            new_version = current_version + 1

            # Create the new database version record
            db_version = DatabaseVersion(
                version=new_version,
                program_id=program_id,
                species=species,
                description=f"Upload of {len(df)} sequences from {project_name}",
                changes_summary=f"Added {len(unique_alleleids) - len(existing_sequences)} new sequences",
                uploaded_by=uploaded_by
            )
            db.add(db_version)
            await db.flush()

            # Create file upload tracking record
            if file_name:
                file_upload = FileUpload(
                    file_name=file_name,
                    upload_type='madc',
                    file_size=file_size,
                    version=new_version,
                    species=species,
                    program_id=program_id,
                    project_name=project_name,
                    uploaded_by=uploaded_by,
                    job_id=job_id
                )
                db.add(file_upload)
                await db.flush()
                logging.info(f"Created file upload tracking record for {file_name}")

            # Prepare lists for bulk insertion
            new_sequences_data = []  # For new Sequence rows
            alleleids_processed = []  # For presence check
            new_sequences = set()

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
                # Batch insert to avoid PostgreSQL parameter limit (32767)
                # Each sequence has 6 parameters, so we can safely insert ~5400 records per batch
                batch_size = 5400  # Conservative limit to stay under 32767 parameters (5400 * 6 = 32400)
                total_batches = (len(new_sequences_data) + batch_size - 1) // batch_size
                
                logging.info(f"Inserting {len(new_sequences_data)} new sequences in {total_batches} batch(es)")
                
                for i in range(0, len(new_sequences_data), batch_size):
                    batch = new_sequences_data[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    logging.info(f"Inserting sequence batch {batch_num}/{total_batches} with {len(batch)} records")
                    
                    try:
                        await db.execute(pg_insert(Sequence).values(batch).on_conflict_do_nothing())
                        
                        # Flush each batch to avoid long-running transactions (except the last one)
                        if batch_num < total_batches:
                            await db.flush()
                            
                    except Exception as batch_error:
                        logging.error(f"Error in sequence batch {batch_num}: {str(batch_error)}")
                        raise batch_error

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
                # Batch insert to avoid PostgreSQL parameter limit (32767)
                # Each SequencePresence has 5 parameters, so we can safely insert ~6500 records per batch
                batch_size = 6500  # Conservative limit to stay under 32767 parameters (6500 * 5 = 32500)
                total_batches = (len(new_presence_data) + batch_size - 1) // batch_size
                
                logging.info(f"Inserting {len(new_presence_data)} new sequence presences in {total_batches} batch(es)")
                
                for i in range(0, len(new_presence_data), batch_size):
                    batch = new_presence_data[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    logging.info(f"Inserting presence batch {batch_num}/{total_batches} with {len(batch)} records")
                    
                    try:
                        await db.execute(pg_insert(SequencePresence).values(batch).on_conflict_do_nothing())
                        
                        # Flush each batch to avoid long-running transactions (except the last one)
                        if batch_num < total_batches:
                            await db.flush()
                            
                    except Exception as batch_error:
                        logging.error(f"Error in presence batch {batch_num}: {str(batch_error)}")
                        raise batch_error

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
            jobs[job_id]['error'] = str(e)
            logging.error(f"Error processing job {job_id}: {str(e)}")
        finally:
            # Ensure the session is properly closed
            await db.close()






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


async def process_pav_upload(file_data: bytes, job_id: str, species: str, program_id: int, file_name: str = None, file_size: int = None, uploaded_by: int = None):
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
            existing_alleles = {row[0] for row in result}
            
            # Log how many alleles were found vs requested
            logging.info(f"Found {len(existing_alleles)} existing alleles out of {len(allele_ids)} unique alleles in CSV")

            # Get the current version number for this species (do not create a new version for PAV uploads)
            stmt = select(func.max(DatabaseVersion.version)).where(DatabaseVersion.species == species)
            result = await db.execute(stmt)
            current_version = result.scalar_one_or_none()
            
            if current_version is None:
                # No existing version found for this species
                logging.error(f"No existing database version found for species '{species}'. PAV data cannot be processed without existing sequence data.")
                raise HTTPException(status_code=400, detail=f"No existing database version found for species '{species}'. Please upload sequence data first.")
            
            # Use the current version for PAV data (do not increment)
            version_to_use = current_version
            logging.info(f"Using existing database version {version_to_use} for PAV data")

            # Verify that this version actually exists in the database_versions table
            stmt = select(DatabaseVersion).where(
                DatabaseVersion.version == version_to_use,
                DatabaseVersion.species == species
            )
            result = await db.execute(stmt)
            version_record = result.scalar_one_or_none()
            
            if version_record is None:
                logging.error(f"Database version {version_to_use} not found in database_versions table for species '{species}'")
                raise HTTPException(status_code=500, detail=f"Database version {version_to_use} not found. Database may be in an inconsistent state.")
            
            logging.info(f"Verified database version {version_to_use} exists (created: {version_record.created_at})")

            # Create file upload tracking record for PAV upload
            if file_name:
                file_upload = FileUpload(
                    file_name=file_name,
                    upload_type='pav',
                    file_size=file_size,
                    version=version_to_use,
                    species=species,
                    program_id=program_id,
                    project_name=None,  # PAV uploads don't have projects
                    uploaded_by=uploaded_by,
                    job_id=job_id
                )
                db.add(file_upload)
                await db.flush()
                logging.info(f"Created PAV file upload tracking record for {file_name}")

            # Pre-build a set of valid (alleleid, accession_id) pairs from the CSV
            # Only include pairs where the AlleleID exists in the Sequence table
            potential_pairs = set()
            for row in df.itertuples(index=False):
                alleleid = getattr(row, 'AlleleID')
                if alleleid not in existing_alleles:
                    continue
                
                accessions_presence = {acc: getattr(row, acc, 0) for acc in accession_names}
                for acc_name, presence in accessions_presence.items():
                    if presence == 1:
                        accession_id = accession_map.get(acc_name)
                        if accession_id is not None:
                            potential_pairs.add((alleleid, accession_id))

            # Fetch existing AllelePresence records for these potential pairs
            existing_presence_pairs = set()
            if potential_pairs:
                # Convert set to lists for the query
                potential_pairs_list = list(potential_pairs)
                allele_ids_to_check = list(set(pair[0] for pair in potential_pairs_list))
                accession_ids_to_check = list(set(pair[1] for pair in potential_pairs_list))
                
                existing_stmt = select(AllelePresence.alleleid, AllelePresence.accession_id).where(
                    AllelePresence.alleleid.in_(allele_ids_to_check),
                    AllelePresence.accession_id.in_(accession_ids_to_check)
                )
                existing_result = await db.execute(existing_stmt)
                existing_presence_pairs = {(row.alleleid, row.accession_id) for row in existing_result}
                
                logging.info(f"Found {len(existing_presence_pairs)} existing AllelePresence records to skip")

            # Accumulate new AllelePresence records (for presence == 1)
            allele_presence_bulk = []
            
            # Tracking counters
            total_processed = 0
            skipped_missing_alleles = 0
            skipped_duplicates = 0

            # Process each row using itertuples for better performance
            for row in df.itertuples(index=False):
                alleleid = getattr(row, 'AlleleID')
                total_processed += 1
                
                if alleleid not in existing_alleles:
                    logging.warning(f"AlleleID '{alleleid}' does not exist in the Sequence table. Skipping.")
                    skipped_missing_alleles += 1
                    continue

                # Build the presence mapping from the row (defaulting to 0 if missing)
                accessions_presence = {acc: getattr(row, acc, 0) for acc in accession_names}

                for acc_name, presence in accessions_presence.items():
                    if presence == 1:
                        accession_id = accession_map.get(acc_name)
                        if accession_id is None:
                            logging.warning(f"Accession '{acc_name}' not found. Skipping.")
                            continue
                        
                        # Check if this combination already exists
                        if (alleleid, accession_id) in existing_presence_pairs:
                            logging.debug(f"AllelePresence record for alleleid='{alleleid}', accession_id={accession_id} already exists. Skipping.")
                            skipped_duplicates += 1
                            continue
                        
                        # Double-check that we have both the AlleleID and AccessionID
                        if alleleid in existing_alleles and accession_id in accession_map.values():
                            allele_presence_bulk.append({
                                "alleleid": alleleid,
                                "species": species,
                                "accession_id": accession_id,
                                "version_added": version_to_use
                            })

            # Log the final counts before insertion
            logging.info(f"Prepared {len(allele_presence_bulk)} records for bulk insertion")

            # Validate the data before insertion
            if allele_presence_bulk:
                # Check for any invalid AlleleIDs that might have slipped through
                bulk_allele_ids = {record['alleleid'] for record in allele_presence_bulk}
                invalid_allele_ids = bulk_allele_ids - existing_alleles
                if invalid_allele_ids:
                    logging.error(f"Found {len(invalid_allele_ids)} invalid AlleleIDs in bulk data: {list(invalid_allele_ids)[:10]}...")
                    # Remove invalid records
                    allele_presence_bulk = [record for record in allele_presence_bulk if record['alleleid'] not in invalid_allele_ids]
                    logging.info(f"Filtered out invalid records, {len(allele_presence_bulk)} records remaining")
                
                # Check for any invalid AccessionIDs
                bulk_accession_ids = {record['accession_id'] for record in allele_presence_bulk}
                valid_accession_ids = set(accession_map.values())
                invalid_accession_ids = bulk_accession_ids - valid_accession_ids
                if invalid_accession_ids:
                    logging.error(f"Found {len(invalid_accession_ids)} invalid AccessionIDs in bulk data: {list(invalid_accession_ids)[:10]}...")
                    # Remove invalid records
                    allele_presence_bulk = [record for record in allele_presence_bulk if record['accession_id'] not in invalid_accession_ids]
                    logging.info(f"Filtered out invalid accession records, {len(allele_presence_bulk)} records remaining")

                # Validate required fields and data integrity
                valid_records = []
                for record in allele_presence_bulk:
                    if (record.get('alleleid') and 
                        record.get('species') == species and 
                        record.get('accession_id') is not None and
                        record.get('version_added') == version_to_use):
                        valid_records.append(record)
                    else:
                        logging.warning(f"Invalid record structure: {record}")
                
                allele_presence_bulk = valid_records
                logging.info(f"After validation, {len(allele_presence_bulk)} valid records remain")
                
                # Final consistency check
                if allele_presence_bulk:
                    # Verify all records use the correct version
                    versions_in_batch = {record['version_added'] for record in allele_presence_bulk}
                    if len(versions_in_batch) > 1 or version_to_use not in versions_in_batch:
                        logging.error(f"Inconsistent versions in batch: {versions_in_batch}, expected: {version_to_use}")
                        raise HTTPException(status_code=500, detail="Inconsistent version numbers in batch data")
                    
                    # Verify all records have the correct species
                    species_in_batch = {record['species'] for record in allele_presence_bulk}
                    if len(species_in_batch) > 1 or species not in species_in_batch:
                        logging.error(f"Inconsistent species in batch: {species_in_batch}, expected: {species}")
                        raise HTTPException(status_code=500, detail="Inconsistent species in batch data")
                    
                    logging.info(f"Final validation passed: {len(allele_presence_bulk)} records ready for insertion")

            # Comprehensive foreign key validation before insertion
            if allele_presence_bulk:
                logging.info("Performing comprehensive foreign key validation...")
                
                # 1. Validate version_added foreign key
                stmt = select(DatabaseVersion.version).where(DatabaseVersion.version == version_to_use)
                result = await db.execute(stmt)
                valid_versions = {row.version for row in result}
                if version_to_use not in valid_versions:
                    logging.error(f"Foreign key validation failed: version_added {version_to_use} not found in database_versions")
                    raise HTTPException(status_code=500, detail=f"Invalid version_added: {version_to_use}")
                logging.info(f"✓ version_added {version_to_use} validated")
                
                # 2. Validate accession_id foreign key
                bulk_accession_ids = list({record['accession_id'] for record in allele_presence_bulk})
                stmt = select(Accession.accession_id).where(Accession.accession_id.in_(bulk_accession_ids))
                result = await db.execute(stmt)
                valid_accession_ids = {row.accession_id for row in result}
                invalid_accessions = set(bulk_accession_ids) - valid_accession_ids
                if invalid_accessions:
                    logging.error(f"Foreign key validation failed: accession_ids not found: {invalid_accessions}")
                    raise HTTPException(status_code=500, detail=f"Invalid accession_ids: {list(invalid_accessions)}")
                logging.info(f"✓ All {len(bulk_accession_ids)} accession_ids validated")
                
                # 3. Validate compound foreign key (alleleid, species) to sequence_table
                bulk_allele_species_pairs = list({(record['alleleid'], record['species']) for record in allele_presence_bulk})
                allele_ids_for_check = [pair[0] for pair in bulk_allele_species_pairs]
                species_for_check = [pair[1] for pair in bulk_allele_species_pairs]
                
                stmt = select(Sequence.alleleid, Sequence.species).where(
                    Sequence.alleleid.in_(allele_ids_for_check),
                    Sequence.species.in_(species_for_check)
                )
                result = await db.execute(stmt)
                valid_allele_species_pairs = {(row.alleleid, row.species) for row in result}
                invalid_pairs = set(bulk_allele_species_pairs) - valid_allele_species_pairs
                if invalid_pairs:
                    logging.error(f"Foreign key validation failed: (alleleid, species) pairs not found in sequence_table: {list(invalid_pairs)[:10]}...")
                    raise HTTPException(status_code=500, detail=f"Invalid (alleleid, species) pairs: {len(invalid_pairs)} found")
                logging.info(f"✓ All {len(bulk_allele_species_pairs)} (alleleid, species) pairs validated")
                
                logging.info("All foreign key validations passed successfully!")

            # Log sample records for debugging
            if allele_presence_bulk:
                sample_size = min(3, len(allele_presence_bulk))
                sample_records = allele_presence_bulk[:sample_size]
                logging.info(f"Sample records to be inserted: {sample_records}")

            # Bulk insert all AllelePresence records (if any)
            inserted_count = 0
            if allele_presence_bulk:
                try:
                    # For very large datasets, split into batches to avoid parameter limits
                    batch_size = 8000  # Each AllelePresence has 4 parameters, so 8000 * 4 = 32000 parameters (under 32767 limit)
                    total_batches = (len(allele_presence_bulk) + batch_size - 1) // batch_size
                    
                    for i in range(0, len(allele_presence_bulk), batch_size):
                        batch = allele_presence_bulk[i:i + batch_size]
                        batch_num = (i // batch_size) + 1
                        
                        logging.info(f"Inserting batch {batch_num}/{total_batches} with {len(batch)} records")
                        
                        try:
                            result = await db.execute(pg_insert(AllelePresence).values(batch).on_conflict_do_nothing())
                            inserted_count += len(batch)
                            
                            # Commit each batch to avoid long-running transactions
                            if batch_num < total_batches:
                                await db.flush()
                                
                        except Exception as batch_error:
                            logging.error(f"Error in batch {batch_num}: {str(batch_error)}")
                            
                            # Log sample records from the failing batch for debugging
                            sample_records = batch[:3] if len(batch) > 3 else batch
                            logging.error(f"Sample records from failing batch: {sample_records}")
                            
                            # Log the exact data structure being inserted
                            logging.error(f"Batch size: {len(batch)}")
                            logging.error(f"First record structure: {batch[0] if batch else 'No records'}")
                            
                            # Verify the records match expected structure
                            expected_keys = {'alleleid', 'species', 'accession_id', 'version_added'}
                            if batch:
                                actual_keys = set(batch[0].keys())
                                if actual_keys != expected_keys:
                                    logging.error(f"Record structure mismatch! Expected: {expected_keys}, Got: {actual_keys}")
                                
                                # Check for any None values or invalid data types
                                for i, record in enumerate(batch[:5]):  # Check first 5 records
                                    for key, value in record.items():
                                        if value is None:
                                            logging.error(f"Found None value in record {i}, field '{key}': {record}")
                                        elif key in ['accession_id', 'version_added'] and not isinstance(value, int):
                                            logging.error(f"Invalid data type in record {i}, field '{key}': {type(value)} = {value}")
                            
                            # Check for specific constraint violations
                            error_str = str(batch_error).lower()
                            if 'foreign key' in error_str:
                                if 'version_added' in error_str:
                                    logging.error(f"Foreign key violation on version_added field. Using version: {version_to_use}")
                                elif 'alleleid' in error_str or 'species' in error_str:
                                    logging.error("Foreign key violation on sequence reference (alleleid, species)")
                                elif 'accession_id' in error_str:
                                    logging.error("Foreign key violation on accession_id")
                            elif 'unique' in error_str or 'duplicate' in error_str:
                                logging.error("Unique constraint violation (duplicate record)")
                            
                            raise batch_error
                    
                    logging.info(f"Successfully processed all {total_batches} batches, {inserted_count} records total")
                except Exception as e:
                    logging.error(f"Error during bulk insert: {str(e)}")
                    logging.error(f"Failed while processing batch with sample record: {allele_presence_bulk[0] if allele_presence_bulk else 'No records'}")
                    raise

            # Final commit: all changes are persisted in one go
            await db.commit()

            # (Optional) Convert the DataFrame back to CSV for download/logging purposes
            output_stream = io.StringIO()
            df.to_csv(output_stream, index=False, header=False)
            output_stream.seek(0)
            jobs_pav[job_id]['file'] = output_stream.getvalue()
            jobs_pav[job_id]['status'] = 'Completed'
            jobs_pav[job_id]['completion_time'] = datetime.utcnow()
            jobs_pav[job_id]['total_rows'] = total_processed
            jobs_pav[job_id]['skipped_missing_alleles'] = skipped_missing_alleles
            jobs_pav[job_id]['skipped_duplicates'] = skipped_duplicates
            jobs_pav[job_id]['records_inserted'] = inserted_count
            logging.info(f"PAV Job {job_id} completed successfully. Processed: {total_processed}, Inserted: {inserted_count}, Skipped (missing alleles): {skipped_missing_alleles}, Skipped (duplicates): {skipped_duplicates}")
        except Exception as e:
            await db.rollback()
            jobs_pav[job_id]['status'] = 'Failed'
            jobs_pav[job_id]['error'] = str(e)
            logging.error(f"Error processing PAV job {job_id}: {str(e)}")
        finally:
            # Ensure the session is properly closed
            await db.close()


@router.post("/upload/preview")
async def preview_upload(
    file: UploadFile = File(...),
    species: str = Form(...),
    db: AsyncSession = Depends(get_session)
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
        logging.error(f"Error in upload preview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/")
async def upload_microhaplotype_data(
        request: Request,
        file: UploadFile = File(...),
        species: str = Form(...),
        program_name: str = Form(...),
        project_name: str = Form(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: AsyncSession = Depends(get_session),
        current_user: User = Depends(require_private_access)
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
    # now passing project_name along with program_id.
    asyncio.create_task(
        process_upload(
            file_data=contents,
            job_id=job_id,
            species=species,
            program_id=program_obj.id,
            project_name=project_name,
            file_name=file.filename,
            file_size=len(contents),
            uploaded_by=current_user.id if current_user else None
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
        db: AsyncSession = Depends(get_session),
        current_user: User = Depends(require_private_access)
):
    """
    Endpoint to upload PAV-formatted microhaplotype data.
    """
    # Validate file type
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Only CSV files are supported for PAV uploads.")

    # Get existing program based on the provided program_name (do not create new programs for PAV uploads)
    result = await db.execute(select(Program).where(Program.name == program_name))
    existing_program = result.scalar_one_or_none()

    if not existing_program:
        raise HTTPException(
            status_code=400, 
            detail=f"Program '{program_name}' not found. PAV uploads can only use existing programs. Please select an existing program or create the program through a regular MADC upload first."
        )
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
                                           species=species, program_id=program_id,
                                           file_name=file.filename,
                                           file_size=len(contents),
                                           uploaded_by=current_user.id if current_user else None))
    logging.info(f"Started PAV processing job {job_id} for file {file.filename}")
    return {"job_id": job_id, "message": "PAV processing started. Check job status."}


@router.get("/report_data")
async def get_report_data(
    species: str = 'all',
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
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
async def download_processed_file(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
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
async def list_jobs(current_user: User = Depends(get_current_user)):
    job_list = [{
        "job_id": job_id,
        "status": job['status'],
        "submission_time": job['submission_time'],
        "completion_time": job.get('completion_time'),
        "file_name": job.get('file_name')  # Include the filename
    } for job_id, job in jobs.items()]

    return job_list


@router.get("/pav_jobStatus", response_model=List[JobStatusResponse])
async def list_pav_jobs(current_user: User = Depends(get_current_user)):
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
async def get_pav_accessions_for_allele(
    alleleid: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
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
async def execute_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
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
        db: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    if request.page < 1:
        raise HTTPException(status_code=400, detail="Page number must be >= 1")

    # Start with the base query
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

    # Apply role-based access control filtering - OPTIMIZED
    if not current_user.is_admin:
        # Pre-compute accessible user IDs to avoid repeated subqueries
        collaborator_ids = [collaboration.user_id for collaboration in current_user.collaborator_in]
        accessible_ids = [current_user.id] + collaborator_ids
        
        # Create a more efficient access control filter
        access_conditions = []
        
        if current_user.role == UserRoleEnum.PUBLIC:
            # Public users can only see data uploaded by public users
            access_conditions.append(
                Sequence.version_added.in_(
                    select(DatabaseVersion.version).where(
                        and_(
                            DatabaseVersion.species == request.species,
                            DatabaseVersion.uploaded_by.in_(
                                select(User.id).where(User.role == UserRoleEnum.PUBLIC)
                            )
                        )
                    )
                )
            )
        else:  # COLLABORATOR or PRIVATE_USER
            # Can see their data, collaborators' data, and public data
            access_conditions.extend([
                Sequence.version_added.in_(
                    select(DatabaseVersion.version).where(
                        and_(
                            DatabaseVersion.species == request.species,
                            DatabaseVersion.uploaded_by.in_(accessible_ids)
                        )
                    )
                ),
                Sequence.version_added.in_(
                    select(DatabaseVersion.version).where(
                        and_(
                            DatabaseVersion.species == request.species,
                            DatabaseVersion.uploaded_by.in_(
                                select(User.id).where(User.role == UserRoleEnum.PUBLIC)
                            )
                        )
                    )
                )
            ])
        
        if access_conditions:
            query = query.where(or_(*access_conditions))

    # Calculate total records using a more efficient count query
    count_query = select(func.count(Sequence.alleleid))
    
    # Apply the same filters to the count query
    if request.species:
        count_query = count_query.where(Sequence.species == request.species)
    
    if request.globalFilter:
        global_search = f"%{request.globalFilter}%"
        count_query = count_query.where(
            or_(
                Sequence.alleleid.ilike(global_search),
                Sequence.allelesequence.ilike(global_search),
                Sequence.species.ilike(global_search),
                Sequence.info.ilike(global_search),
                Sequence.associated_trait.ilike(global_search)
            )
        )
    
    if request.filters:
        for field, filter_obj in request.filters.items():
            if filter_obj.value:
                if field == 'alleleid':
                    count_query = count_query.where(Sequence.alleleid.ilike(f"%{filter_obj.value}%"))
                elif field == 'allelesequence':
                    count_query = count_query.where(Sequence.allelesequence.ilike(f"%{filter_obj.value}%"))
                elif field == 'info':
                    count_query = count_query.where(Sequence.info.ilike(f"%{filter_obj.value}%"))
                elif field == 'associated_trait':
                    count_query = count_query.where(Sequence.associated_trait.ilike(f"%{filter_obj.value}%"))
    
    # Apply the same access control filters to count query
    if not current_user.is_admin:
        # Pre-compute accessible user IDs to avoid repeated subqueries
        collaborator_ids = [collaboration.user_id for collaboration in current_user.collaborator_in]
        accessible_ids = [current_user.id] + collaborator_ids
        
        # Create a more efficient access control filter
        access_conditions = []
        
        if current_user.role == UserRoleEnum.PUBLIC:
            # Public users can only see data uploaded by public users
            access_conditions.append(
                Sequence.version_added.in_(
                    select(DatabaseVersion.version).where(
                        and_(
                            DatabaseVersion.species == request.species,
                            DatabaseVersion.uploaded_by.in_(
                                select(User.id).where(User.role == UserRoleEnum.PUBLIC)
                            )
                        )
                    )
                )
            )
        else:  # COLLABORATOR or PRIVATE_USER
            # Can see their data, collaborators' data, and public data
            access_conditions.extend([
                Sequence.version_added.in_(
                    select(DatabaseVersion.version).where(
                        and_(
                            DatabaseVersion.species == request.species,
                            DatabaseVersion.uploaded_by.in_(accessible_ids)
                        )
                    )
                ),
                Sequence.version_added.in_(
                    select(DatabaseVersion.version).where(
                        and_(
                            DatabaseVersion.species == request.species,
                            DatabaseVersion.uploaded_by.in_(
                                select(User.id).where(User.role == UserRoleEnum.PUBLIC)
                            )
                        )
                    )
                )
            ])
        
        if access_conditions:
            count_query = count_query.where(or_(*access_conditions))

    total_result = await db.execute(count_query)
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
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if not request.alleleid:
        raise HTTPException(
            status_code=400,
            detail="List of alleleid cannot be empty."
        )

    # Build query that joins AllelePresence -> Accession -> Sequence -> SequencePresence -> Program
    # and left outer joins Program to Project via the association table.
    stmt = (
        select(
            AllelePresence.alleleid,
            Accession.accession_name,
            Program.name.label("program_name"),
            Project.name.label("project_name")
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
        # Left outer join to get Project info (if any)
        .outerjoin(program_project_association, Program.id == program_project_association.c.program_id)
        .outerjoin(Project, program_project_association.c.project_id == Project.id)
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
                "projects": set()
            }
        if row.program_name:
            mapping[key]["programs"].add(row.program_name)
        if row.project_name:
            mapping[key]["projects"].add(row.project_name)

    # Log the details for each aggregated record
    for item in mapping.values():
        logging.info(
            "AlleleID: %s, Accession: %s, Programs: %s, Projects: %s",
            item["alleleid"],
            item["accession"],
            sorted(list(item["programs"])),
            sorted(list(item["projects"]))
        )

    # Prepare the response: flatten the sets into sorted lists
    response = []
    for item in mapping.values():
        response.append(AccessionDetailResponse(
            alleleid=item["alleleid"],
            accession=item["accession"],
            programs=sorted(list(item["programs"])),
            projects=sorted(list(item["projects"]))
        ))
    return response



@router.post("/alleleDetails", response_model=PaginatedSequenceResponse)
async def get_alleleDetails(
        request: PaginatedSequenceRequest,
        db: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
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
async def get_sequences_for_alignment(
    filter: str = "",
    filter_field: str = "",
    species: str = "",
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
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
async def get_programs(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    programs = await db.execute(select(Program))
    program_list = programs.scalars().all()
    return {"programs": [{"id": program.id, "name": program.name} for program in program_list]}


class ProgramCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


@router.post("/programs/create")
async def create_program(
    request: ProgramCreateRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_access)
):
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


@router.get("/projects/list", response_model=List[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    projects = await db.execute(select(Project))
    project_list = projects.scalars().all()
    return project_list


@router.get("/projects/by_program/{program_id}")
async def get_projects_by_program(
    program_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get projects associated with a specific program.
    """
    try:
        # Use the association table to find projects linked to this program
        stmt = (
            select(Project)
            .join(program_project_association, Project.id == program_project_association.c.project_id)
            .where(program_project_association.c.program_id == program_id)
            .order_by(Project.name)
        )

        result = await db.execute(stmt)
        projects = result.scalars().all()

        return [{"id": project.id, "name": project.name, "value": project.name} for project in projects]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving projects: {str(e)}")


@router.get("/projects/by_program_name/{program_name}")
async def get_projects_by_program_name(
    program_name: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get projects associated with a specific program by program name.
    """
    try:
        # First find the program by name
        stmt = select(Program).where(Program.name == program_name)
        result = await db.execute(stmt)
        program = result.scalars().first()
        
        if not program:
            raise HTTPException(status_code=404, detail=f"Program with name '{program_name}' not found")
        
        # Use the association table to find projects linked to this program
        stmt = (
            select(Project)
            .join(program_project_association, Project.id == program_project_association.c.project_id)
            .where(program_project_association.c.program_id == program.id)
            .order_by(Project.name)
        )

        result = await db.execute(stmt)
        projects = result.scalars().all()

        return [{"id": project.id, "name": project.name, "value": project.name} for project in projects]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving projects: {str(e)}")


@router.post("/projects/create")
async def create_project(
    project: ProjectCreate,
    program_name: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_access)
):
    try:
        # Check if any project with this name already exists (for warning purposes) - more efficient query
        existing_project_count = await db.execute(
            select(func.count(Project.id)).where(Project.name == project.name)
        )
        has_existing_projects = existing_project_count.scalar() > 0

        # Create the new project
        new_project = Project(name=project.name, description=project.description)
        db.add(new_project)
        await db.flush()  # Get the project ID
        
        # If a program_name is provided, associate the project with that program
        if program_name:
            # Find the program by name - avoid expensive selectinload
            stmt = select(Program.id, Program.name).where(Program.name == program_name)
            result = await db.execute(stmt)
            program_row = result.first()
            
            if program_row:
                program_id = program_row.id
                
                # Check if this program already has a project with the same name - efficient query
                existing_association_count = await db.execute(
                    select(func.count(program_project_association.c.program_id)).where(
                        and_(
                            program_project_association.c.program_id == program_id,
                            program_project_association.c.project_id.in_(
                                select(Project.id).where(Project.name == project.name)
                            )
                        )
                    )
                )
                program_has_project = existing_association_count.scalar() > 0
                
                if not program_has_project:
                    # Check if the exact association already exists to avoid duplicates
                    existing_exact_association = await db.execute(
                        select(func.count(program_project_association.c.program_id)).where(
                            and_(
                                program_project_association.c.program_id == program_id,
                                program_project_association.c.project_id == new_project.id
                            )
                        )
                    )
                    
                    if existing_exact_association.scalar() == 0:
                        # Create the association
                        await db.execute(
                            program_project_association.insert().values(
                                program_id=program_id,
                                project_id=new_project.id
                            )
                        )
                        logging.info(f"Associated project '{project.name}' with program '{program_name}'")
                else:
                    logging.warning(f"Program '{program_name}' already has a project named '{project.name}'")
            else:
                logging.warning(f"Program '{program_name}' not found for project association")
        
        # Single commit for all operations
        await db.commit()
        await db.refresh(new_project)

        # Convert to dict for response
        response_dict = {
            "id": new_project.id,
            "name": new_project.name,
            "description": new_project.description,
            "created_at": new_project.created_at,
            "warning": None
        }
        
        # Add warning if duplicate name exists
        if has_existing_projects:
            response_dict["warning"] = f"A project with the name '{project.name}' already exists."
        
        return response_dict

    except IntegrityError as e:
        await db.rollback()
        logging.error(f"IntegrityError creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create project due to a database error: {str(e)}")
    except Exception as e:
        await db.rollback()
        logging.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")
    finally:
        # Ensure the session is properly closed
        await db.close()


@router.post("/supplemental_upload/")
async def upload_supplemental_data(
        request: Request,
        file: UploadFile = File(...),
        species: str = Form(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: AsyncSession = Depends(get_session),
        current_user: User = Depends(require_private_access)
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
        species=species,
        file_name=file.filename,
        file_size=len(contents),
        uploaded_by=current_user.id if current_user else None
    ))

    return {"job_id": job_id, "message": "Supplemental processing started. Check job status."}


async def process_supplemental_upload(file_data: bytes, job_id: str, species: str, file_name: str = None, file_size: int = None, uploaded_by: int = None):
    """
    Background task to process supplemental upload CSV.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Get the current version for this species to associate file tracking
            stmt = select(func.max(DatabaseVersion.version)).where(DatabaseVersion.species == species)
            result = await db.execute(stmt)
            current_version = result.scalar_one_or_none()
            
            if current_version is None:
                logging.error(f"No database version found for species '{species}'. Cannot process supplemental upload.")
                jobs_supplemental[job_id]['status'] = 'Failed'
                jobs_supplemental[job_id]['error'] = f"No database version found for species '{species}'"
                return

            # Create file upload tracking record for supplemental upload
            if file_name:
                file_upload = FileUpload(
                    file_name=file_name,
                    upload_type='supplemental',
                    file_size=file_size,
                    version=current_version,
                    species=species,
                    program_id=1,  # Use a default program ID for supplemental uploads since they don't require program selection
                    project_name=None,  # Supplemental uploads don't have projects
                    uploaded_by=uploaded_by,
                    job_id=job_id
                )
                db.add(file_upload)
                await db.flush()
                logging.info(f"Created supplemental file upload tracking record for {file_name}")

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
        finally:
            # Ensure the session is properly closed
            await db.close()


@router.get("/supplemental_jobStatus", response_model=List[SupplementalJobStatusResponse])
async def list_supplemental_jobs(current_user: User = Depends(get_current_user)):
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
        db: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
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
        db: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
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
        db: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
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
    request: Request,
    program_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get the count of unique alleleIDs for each database version of the specified species.
    Optionally filter by program ID. OPTIMIZED VERSION.
    """
    try:
        # Build query dynamically based on whether program_id is provided
        if program_id is not None:
            # Query with program filter
            base_query = text("""
                WITH version_stats AS (
                    SELECT 
                        dv.version,
                        dv.species,
                        dv.created_at,
                        dv.description,
                        dv.program_id,
                        p.name as program_name,
                        COUNT(DISTINCT s.alleleid) as new_alleles,
                        SUM(COUNT(DISTINCT s.alleleid)) OVER (
                            ORDER BY dv.version ROWS UNBOUNDED PRECEDING
                        ) as total_alleles
                    FROM database_versions dv
                    JOIN programs p ON dv.program_id = p.id
                    LEFT JOIN sequence_table s ON s.version_added = dv.version AND s.species = dv.species
                    WHERE dv.species = :species
                        AND dv.program_id = :program_id
                    GROUP BY dv.version, dv.species, dv.created_at, dv.description, dv.program_id, p.name
                    ORDER BY dv.version
                )
                SELECT * FROM version_stats
            """)
            query_params = {"species": species, "program_id": program_id}
        else:
            # Query without program filter
            base_query = text("""
                WITH version_stats AS (
                    SELECT 
                        dv.version,
                        dv.species,
                        dv.created_at,
                        dv.description,
                        dv.program_id,
                        p.name as program_name,
                        COUNT(DISTINCT s.alleleid) as new_alleles,
                        SUM(COUNT(DISTINCT s.alleleid)) OVER (
                            ORDER BY dv.version ROWS UNBOUNDED PRECEDING
                        ) as total_alleles
                    FROM database_versions dv
                    JOIN programs p ON dv.program_id = p.id
                    LEFT JOIN sequence_table s ON s.version_added = dv.version AND s.species = dv.species
                    WHERE dv.species = :species
                    GROUP BY dv.version, dv.species, dv.created_at, dv.description, dv.program_id, p.name
                    ORDER BY dv.version
                )
                SELECT * FROM version_stats
            """)
            query_params = {"species": species}

        # Execute the optimized query
        result = await session.execute(base_query, query_params)
        versions = result.fetchall()

        if not versions:
            return []

        # Build response data
        response_data = []
        
        for version_row in versions:
            # Get file uploads for this version - use a more efficient query
            files_query = (
                select(FileUpload)
                .options(selectinload(FileUpload.program), selectinload(FileUpload.user))
                .where(
                    FileUpload.version == version_row.version,
                    FileUpload.species == species
                )
                .order_by(FileUpload.upload_date)
            )
            
            files_result = await session.execute(files_query)
            files = files_result.scalars().all()
            
            # Convert files to response format
            file_responses = []
            for file_upload in files:
                file_responses.append({
                    "id": file_upload.id,
                    "file_name": file_upload.file_name,
                    "upload_type": file_upload.upload_type,
                    "file_size": file_upload.file_size,
                    "upload_date": file_upload.upload_date,
                    "version": file_upload.version,
                    "species": file_upload.species,
                    "program_name": file_upload.program.name if file_upload.program else None,
                    "project_name": file_upload.project_name,
                    "uploaded_by": file_upload.user.full_name if file_upload.user else None
                })
            
            response_data.append(
                VersionStatsResponse(
                    version=version_row.version,
                    species=version_row.species,
                    created_at=version_row.created_at,
                    total_alleles=int(version_row.total_alleles or 0),
                    new_alleles=int(version_row.new_alleles or 0),
                    program_name=version_row.program_name,
                    description=version_row.description,
                    files=file_responses
                )
            )

        return response_data

    except Exception as e:
        logging.error(f"Error retrieving version statistics for {species}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving version statistics: {str(e)}")


@router.get("/programs/", response_model=List[ProgramResponse])
async def get_programs(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
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
        logging.error(f"Error retrieving programs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving programs: {str(e)}")


@router.get("/database_version/{species}", response_model=dict)
async def get_latest_database_version(
    species: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get the latest database version for a given species.
    """
    try:
        # More efficient approach using a single query with sorting and limit
        query = select(DatabaseVersion).where(
            DatabaseVersion.species == species.lower()
        ).order_by(
            DatabaseVersion.version.desc()
        ).limit(1)

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


@router.get("/accessible-data")
async def get_accessible_data(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get information about the user's access level and accessible data.
    This is used by the frontend to filter data based on the user's access level.
    """
    if current_user.is_admin:
        return {
            "access_level": "admin",
            "accessible_user_ids": None  # None indicates access to all users
        }
    
    accessible_ids = [current_user.id]
    
    # Get users who have collaborated with the current user
    # Use eagerly loaded relationship data instead of executing additional query
    collaborator_ids = [collaboration.user_id for collaboration in current_user.collaborator_in]
    accessible_ids.extend(collaborator_ids)
    
    return {
        "access_level": current_user.role,
        "accessible_user_ids": accessible_ids
    }


@router.get("/programs/by_species/{species}")
async def get_programs_by_species(
    species: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of programs that have sequences for a specific species.
    """
    try:
        # Optimized query using EXISTS instead of joins
        stmt = text("""
            SELECT DISTINCT p.id, p.name
            FROM programs p
            WHERE EXISTS (
                SELECT 1
                FROM sequence_presence sp
                JOIN sequence_table s ON sp.alleleid = s.alleleid AND sp.species = s.species
                WHERE sp.program_id = p.id AND s.species = :species
            )
            ORDER BY p.name;
        """)

        result = await db.execute(stmt, {"species": species})
        programs = result.fetchall()

        return {"programs": [{"id": program.id, "name": program.name} for program in programs]}
    except Exception as e:
        logging.error(f"Error retrieving programs for species {species}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving programs: {str(e)}")
