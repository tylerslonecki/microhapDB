# src/main.py or equivalent

from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from src.auth.router import router as auth_router
from src.aws.router import router as aws_router
from src.posts.router import router as posts_router
from src.models import init_db, AsyncSessionLocal, AllowedOrcid
from fastapi.middleware.cors import CORSMiddleware
from src.auth.dependencies import get_current_user, get_admin_user
from src.auth.models import UserResponse
import asyncio
from datetime import datetime, timedelta
import time
from sqlalchemy.future import select

from src.posts.router import jobs


app = FastAPI(title="Microhaplotype Database", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://microhapdb.loca.lt"],  # Frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(aws_router, prefix="/aws", tags=["AWS Integration"])
app.include_router(posts_router, prefix="/posts", tags=["Posts"])

def remove_old_jobs():
    while True:
        now = datetime.utcnow()
        for job_id in list(jobs.keys()):
            job = jobs[job_id]
            if job['status'] == 'completed' and 'completion_time' in job:
                if now - job['completion_time'] > timedelta(minutes=30):  # Keep jobs for 30 minutes after completion
                    del jobs[job_id]
        time.sleep(60)  # Run cleanup every 60 seconds

@app.on_event("startup")
async def startup_event():
    await init_db()
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, remove_old_jobs)
    await initialize_allowed_orcids()

async def initialize_allowed_orcids():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(select(AllowedOrcid))
            allowed_orcids = result.scalars().all()
            if not allowed_orcids:
                session.add_all([
                    AllowedOrcid(orcid='0000-0002-4762-3518', is_admin=True),
                    # Add other allowed ORCIDs here
                ])
                await session.commit()

import os
print("Current Working Directory:", os.getcwd())

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/login")
def redirect_to_login():
    return RedirectResponse(url="/auth/login")

@app.get("/protected-route", response_model=UserResponse)
async def protected_route(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@app.get("/admin-route", response_model=UserResponse)
async def admin_route(admin_user: UserResponse = Depends(get_admin_user)):
    return admin_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
