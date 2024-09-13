import uuid
from typing import List, Dict
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Response, Request, BackgroundTasks, Form
from starlette.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .models import Sequence, get_session, get_sync_session, UploadBatch, SequenceLog, JobStatusResponse, \
    SyncSessionLocal, QueryRequest, PaginatedSequenceResponse, SequenceResponse, PaginatedSequenceRequest
from .service import get_all_batch_summaries, get_new_sequences_for_batch, get_total_unique_sequences, generate_upset_plot, generate_line_chart
import pandas as pd
import io
import os
from datetime import datetime, timedelta
from sqlalchemy import func, text
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


def process_upload(file_data, job_id, db_session_factory, species):
    db = db_session_factory()
    try:
        df = pd.read_csv(io.StringIO(file_data.decode('utf-8')), header=None, low_memory=False)

        batch = UploadBatch()
        db.add(batch)
        db.commit()

        # Insert the 'hapid' column at the correct position (second column, after the first)
        if 'hapid' not in df.columns:
            df.insert(0, 'hapid', '*')  # Initialize with '*'
            df.iloc[7, 0] = "hapid"

        # Process rows starting from the 8th (index 7 in zero-indexed Python)
        for index in range(8, len(df)):
            alleleid = df.iloc[index, 1]  # Assuming alleleid is in the first column
            allelesequence = df.iloc[index, 3]  # Assuming allelesequence is in the third column

            # Check for existing sequence
            existing = db.query(Sequence).filter_by(allelesequence=allelesequence, species=species).first()

            if not existing:
                # Add new microhaplotype if not exists
                new_hap = Sequence(
                    alleleid=alleleid,
                    allelesequence=allelesequence,
                    species=species
                )
                db.add(new_hap)
                db.commit()
                was_new = True
                hapid = new_hap.hapid
                # print(f"Added new microhaplotype: {allelesequence}")

            else:
                hapid = existing.hapid
                was_new = False
                # print(f"Sequence already exists: {allelesequence}")

            log_entry = SequenceLog(hapid=hapid, batch_id=batch.id, was_new=was_new, species=species)
            db.add(log_entry)
            db.commit()
            df.at[index, 'hapid'] = hapid  # Append hapid to column data

        # Convert DataFrame back to CSV
        output_stream = io.StringIO()
        df.to_csv(output_stream, index=False, header=False)
        output_stream.seek(0)
        output_csv = output_stream.getvalue().encode('utf-8')
        jobs[job_id]['file'] = output_stream.getvalue()
        jobs[job_id]['status'] = 'Completed'
        jobs[job_id]['completion_time'] = datetime.utcnow()
    except Exception as e:
        db.rollback()
        jobs[job_id]['status'] = 'Failed'
        print(f"Error processing job {job_id}: {str(e)}")
    finally:
        db.close()

@router.post("/upload/")
async def upload_microhaplotype_data(
    request: Request,
    file: UploadFile = File(...),
    species: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_sync_session)
):
    # user = await get_current_user(request, db)  # Pass request and db explicitly
    # logging.info(user)
    # if not user.is_admin:
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    job_id = str(uuid4())
    contents = await file.read()
    jobs[job_id] = {'status': 'Processing', 'submission_time': datetime.utcnow()}
    background_tasks.add_task(process_upload, file_data=contents, job_id=job_id, db_session_factory=SyncSessionLocal, species=species)

    return {"message": "Processing started. Check job status."}


@router.get("/report_data")
async def get_report_data(db: AsyncSession = Depends(get_session)):
    try:
        total_unique_sequences = await get_total_unique_sequences(db)
        new_sequences_this_batch = await get_new_sequences_for_batch(db)
        batch_history = await get_all_batch_summaries(db)
        line_chart_base64 = await generate_line_chart(db)

        return {
            "total_unique_sequences": total_unique_sequences,
            "new_sequences_this_batch": new_sequences_this_batch,
            "batch_history": batch_history,
            "line_chart": line_chart_base64
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
async def execute_query(request: QueryRequest, db: Session = Depends(get_sync_session)):
    query = request.query
    if not is_safe_query(query):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
    try:
        result = db.execute(query).fetchall()
        return {"result": [dict(row) for row in result]}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/sequences", response_model=PaginatedSequenceResponse)
async def get_sequences(request: PaginatedSequenceRequest, db: Session = Depends(get_sync_session)):
    query = db.query(Sequence)

    # Filter by species if provided
    if request.species:
        query = query.filter(Sequence.species == request.species)

    # Apply filter based on filter_field
    if request.filter and request.filter_field:
        if request.filter_field == 'hapid':
            try:
                # Ensure the filter is treated as a UUID and apply an exact match
                uuid.UUID(request.filter)
                query = query.filter(Sequence.hapid == request.filter)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid UUID format for hapid")
        elif request.filter_field == 'alleleid':
            query = query.filter(Sequence.alleleid.ilike(f"%{request.filter}%"))
        elif request.filter_field == 'allelesequence':
            query = query.filter(Sequence.allelesequence.ilike(f"%{request.filter}%"))

    total = query.count()
    sequences = query.offset((request.page - 1) * request.size).limit(request.size).all()

    return PaginatedSequenceResponse(
        total=total,
        items=[SequenceResponse(
            id=str(seq.id),
            hapid=str(seq.hapid),
            alleleid=seq.alleleid,
            allelesequence=seq.allelesequence,
            species=seq.species
        ) for seq in sequences]
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