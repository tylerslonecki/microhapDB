from typing import List, Dict
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Response, Request, BackgroundTasks
from starlette.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .models import Sequence, get_session, get_sync_session, UploadBatch, SequenceLog, JobStatusResponse, SyncSessionLocal
from .service import get_all_batch_summaries, get_new_sequences_for_batch, get_total_unique_sequences, \
    generate_upset_plot, generate_line_chart
import pandas as pd
import io
import os
from datetime import datetime, timedelta
from sqlalchemy import func
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


def process_upload(file_data, job_id, db_session_factory):
    db = db_session_factory()
    try:
        df = pd.read_csv(io.StringIO(file_data.decode('utf-8')), header=None, low_memory=False)

        batch = UploadBatch()
        db.add(batch)
        db.commit()

        # Insert the 'HapUUID' column at the correct position (second column, after the first)
        if 'HapID' not in df.columns:
            df.insert(0, 'HapID', '*')  # Initialize with '*'
            df.iloc[7, 0] = "HapID"

        # Process rows starting from the 8th (index 7 in zero-indexed Python)
        for index in range(8, len(df)):
            alleleId = df.iloc[index, 1]  # Assuming AlleleID is in the first column
            alleleSequence = df.iloc[index, 3]  # Assuming AlleleSequence is in the third column

            # Check for existing sequence
            existing = db.query(Sequence).filter_by(alleleSequence=alleleSequence).first()

            if not existing:
                # Add new microhaplotype if not exists
                new_hap = Sequence(
                    alleleID=alleleId,
                    alleleSequence=alleleSequence
                )
                db.add(new_hap)
                db.commit()
                was_new = True
                hapID = new_hap.hapID
                # print(f"Added new microhaplotype: {alleleSequence}")

            else:
                hapID = existing.hapID
                was_new = False
                # print(f"Sequence already exists: {alleleSequence}")

            log_entry = SequenceLog(hapID=hapID, batch_id=batch.id, was_new=was_new)
            db.add(log_entry)
            db.commit()
            df.at[index, 'HapID'] = hapID  # Append HapID to column data

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
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_sync_session)
):
    user = await get_current_user(request, db)  # Pass request and db explicitly
    logging.info(user)
    # if not user.is_admin:
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    job_id = str(uuid4())
    contents = await file.read()
    jobs[job_id] = {'status': 'Processing', 'submission_time': datetime.utcnow()}
    background_tasks.add_task(process_upload, file_data=contents, job_id=job_id, db_session_factory=SyncSessionLocal)

    return {"message": "Processing started. Check job status."}

    # try:
    # 
    #     job_id = str(uuid4())
    #     # Load the CSV file into a DataFrame
    #     contents = await file.read()
    #     df = pd.read_csv(io.StringIO(contents.decode('utf-8')), header=None)
    # 
    #     batch = UploadBatch()
    #     db.add(batch)
    #     db.commit()
    # 
    #     # Insert the 'HapUUID' column at the correct position (second column, after the first)
    #     if 'HapID' not in df.columns:
    #         df.insert(0, 'HapID', '*')  # Initialize with '*'
    #         df.iloc[7, 0] = "HapID"
    # 
    #     # Process rows starting from the 8th (index 7 in zero-indexed Python)
    #     for index in range(8, len(df)):
    #         alleleId = df.iloc[index, 1]  # Assuming AlleleID is in the first column
    #         alleleSequence = df.iloc[index, 3]  # Assuming AlleleSequence is in the third column
    # 
    #         # Check for existing sequence
    #         existing = db.query(Sequence).filter_by(alleleSequence=alleleSequence).first()
    # 
    #         if not existing:
    #             # Add new microhaplotype if not exists
    #             new_hap = Sequence(
    #                 alleleID=alleleId,
    #                 alleleSequence=alleleSequence
    #             )
    #             db.add(new_hap)
    #             db.commit()
    #             was_new = True
    #             hapID = new_hap.hapID
    #             print(f"Added new microhaplotype: {alleleSequence}")
    # 
    #         else:
    #             hapID = existing.hapID
    #             was_new = False
    #             print(f"Sequence already exists: {alleleSequence}")
    # 
    #         log_entry = SequenceLog(hapID=hapID, batch_id=batch.id, was_new=was_new)
    #         db.add(log_entry)
    #         db.commit()
    #         df.at[index, 'HapID'] = hapID  # Append HapID to column data
    # 
    # except Exception as e:
    #     db.rollback()
    #     raise HTTPException(status_code=500, detail=str(e))
    # finally:
    #     db.close()
    # 
    # # Convert DataFrame back to CSV
    # output_stream = io.StringIO()
    # df.to_csv(output_stream, index=False, header=False)
    # output_stream.seek(0)
    # output_csv = output_stream.getvalue().encode('utf-8')
    # 
    # # Add the report generation to background tasks
    # background_tasks.add_task(generate_report, request)
    # 
    # # Return CSV as a response
    # return Response(content=output_csv, media_type="text/csv", headers={
    #     "Content-Disposition": "attachment; filename=modified_data.csv"
    # })

@router.get("/report", response_class=HTMLResponse)
async def generate_report(request: Request, db: AsyncSession = Depends(get_session)):
    global last_report_time
    global cached_report

    if cached_report is None or await check_new_data_since_last_report(db, last_report_time):
        total_unique_sequences = await get_total_unique_sequences(db)
        new_sequences_this_batch = await get_new_sequences_for_batch(db)
        batch_history = await get_all_batch_summaries(db)
        line_chart_base64 = await generate_line_chart(db)

        cached_report = templates.TemplateResponse("report_template.html", {
            "request": request,
            "total_unique_sequences": total_unique_sequences,
            "new_sequences_this_batch": new_sequences_this_batch,
            "batch_history": batch_history,
            "line_chart": line_chart_base64
        })

        last_report_time = datetime.utcnow()

    return cached_report

# @router.get("/report", response_class=HTMLResponse)
# async def generate_report(request: Request, db: AsyncSession = Depends(get_session)):
#     global last_report_time
#     global cached_report
#
#     # Check if new data has been added since the last report was generated
#     if cached_report is None or await check_new_data_since_last_report(db, last_report_time):
#         total_unique_sequences = get_total_unique_sequences(db)
#         new_sequences_this_batch = get_new_sequences_for_batch(db)
#         batch_history = get_all_batch_summaries(db)
#         line_chart_base64 = generate_line_chart(db)
#
#         # Generate the new report and update the cache
#         cached_report = templates.TemplateResponse("report_template.html", {
#             "request": request,
#             "total_unique_sequences": total_unique_sequences,
#             "new_sequences_this_batch": new_sequences_this_batch,
#             "batch_history": batch_history,
#             "line_chart": line_chart_base64
#         })
#
#         # Update the timestamp when the report was last generated
#         last_report_time = datetime.utcnow()
#
#     return cached_report


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

