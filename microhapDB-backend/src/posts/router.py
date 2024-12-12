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
from .models import Sequence, get_session, UploadBatch, SequenceLog, Project, SequencePresence, \
    JobStatusResponse, \
    QueryRequest, PaginatedSequenceResponse, SequenceResponse, PaginatedSequenceRequest, \
    AsyncSessionLocal, ColumnFilter
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



async def process_upload(file_data, job_id, species, project_id):
    async with AsyncSessionLocal() as db:
        try:
            df = pd.read_csv(io.StringIO(file_data.decode('utf-8')), header=None, low_memory=False)
            version = await get_next_version_number(db, species)
            batch = UploadBatch(project_id=project_id, species=species, version=version)
            db.add(batch)
            await db.flush()  # Flush to get batch.id

            # Ensure 'hapid' column exists
            if 'hapid' not in df.columns:
                df.insert(0, 'hapid', '*')
                df.iloc[7, 0] = "hapid"

            for index in range(8, len(df)):
                alleleid = df.iloc[index, 1]
                allelesequence = df.iloc[index, 3]

                # Check for existing sequence
                stmt = select(Sequence).where(
                    Sequence.allelesequence == allelesequence,
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
                    # Sequence was inserted by another transaction
                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()
                    hapid = existing.hapid
                    was_new = False

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
                    SequencePresence.project_id == project_id,
                    SequencePresence.hapid == hapid,
                    SequencePresence.species == species
                )
                result = await db.execute(presence_stmt)
                presence_entry = result.scalar_one_or_none()

                if not presence_entry:
                    # Add new presence record
                    presence_entry = SequencePresence(
                        project_id=project_id,
                        hapid=hapid,
                        presence=True,
                        species=species
                    )
                    db.add(presence_entry)

                # Update DataFrame
                df.at[index, 'hapid'] = hapid

            # Commit transaction after all operations
            await db.commit()

            # Convert DataFrame back to CSV
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




@router.post("/upload/")
async def upload_microhaplotype_data(
        request: Request,
        file: UploadFile = File(...),
        species: str = Form(...),
        project_name: str = Form(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: AsyncSession = Depends(get_session)
):
    # Get or create project based on the provided project_name
    result = await db.execute(select(Project).filter(Project.name == project_name))
    existing_project = result.scalar_one_or_none()

    if not existing_project:
        new_project = Project(name=project_name)
        db.add(new_project)
        await db.commit()
        await db.refresh(new_project)
        project_id = new_project.id
    else:
        project_id = existing_project.id

    job_id = str(uuid4())
    contents = await file.read()
    jobs[job_id] = {'status': 'Processing', 'submission_time': datetime.utcnow()}

    # Add project_id to the background task
    asyncio.create_task(process_upload(file_data=contents, job_id=job_id,
                                       species=species, project_id=project_id))
    return {"message": "Processing started. Check job status."}



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
        "completion_time": job.get('completion_time')
    } for job_id, job in jobs.items()]

    return job_list

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
                Sequence.species.ilike(global_search)
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
                species=seq.species
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


@router.get("/projects/list")
async def get_projects(db: AsyncSession = Depends(get_session)):
    projects = await db.execute(select(Project))
    project_list = projects.scalars().all()
    return {"projects": [{"id": project.id, "name": project.name} for project in project_list]}


class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

@router.post("/projects/create")
async def create_project(request: ProjectCreateRequest, db: AsyncSession = Depends(get_session)):
    # Check if a project with the same name already exists
    result = await db.execute(select(Project).filter(Project.name == request.name))
    existing_project = result.scalar_one_or_none()

    if existing_project:
        raise HTTPException(status_code=400, detail="Project with this name already exists.")

    # Create a new project instance
    new_project = Project(name=request.name, description=request.description)
    db.add(new_project)

    try:
        await db.commit()
        await db.refresh(new_project)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create project due to a database error.")

    return {"project": {"id": new_project.id, "name": new_project.name, "description": new_project.description}}
