# src/main.py or equivalent

# Load environment variables from .env file
import os
from pathlib import Path
from dotenv import load_dotenv
import logging  # Import standard logging module

# Load .env file from the same directory as main.py
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, Depends, status
from fastapi.responses import RedirectResponse, JSONResponse
from src.auth.router import router as auth_router
from src.aws.router import router as aws_router
from src.posts.router import router as posts_router
from src.models import AdminOrcid, User
from src.database import init_db, AsyncSessionLocal
from fastapi.middleware.cors import CORSMiddleware
from src.auth.dependencies import get_current_user, get_admin_user
from src.auth.models import UserResponse
import asyncio
from datetime import datetime, timedelta
import time
from sqlalchemy.future import select
from src.auth.models import UserRoleEnum
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import MissingGreenlet, SQLAlchemyError
from starlette.responses import Response

from src.posts.router import jobs


app = FastAPI(title="Microhaplotype Database", version="0.1.0")

# Add middleware to handle SQLAlchemy async context
class SQLAlchemyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            return response
        except MissingGreenlet as e:
            # Log the error for debugging
            logging.error(f"MissingGreenlet error: {str(e)}")
            # Return a more user-friendly error
            return JSONResponse(
                content={"detail": "Database operation error. Please try again later."},
                status_code=500
            )

app.add_middleware(SQLAlchemyMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  # Vue.js development server
        "http://localhost:8081",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "https://db18-2601-743-380-20f0-1114-4d5c-5670-5d54.ngrok-free.app",
        os.getenv("FRONTEND_URL", "http://localhost:8080"),
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=3600
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(aws_router, prefix="/aws", tags=["AWS Integration"])
app.include_router(posts_router, prefix="/posts", tags=["Posts"])


async def remove_old_jobs():
    while True:
        now = datetime.utcnow()
        for job_id in list(jobs.keys()):
            job = jobs[job_id]
            # Check for jobs with status 'Completed' or 'Failed'
            if job['status'].lower() in ['completed', 'failed'] and 'completion_time' in job:
                # Remove if the job was completed more than 5 minutes ago
                if now - job['completion_time'] > timedelta(minutes=5):
                    del jobs[job_id]
                    logging.info(f"Job {job_id} removed after 5 minutes.")
        await asyncio.sleep(60)  # Run cleanup every 60 seconds

@app.on_event("startup")
async def startup_event():
    await init_db()
    asyncio.create_task(remove_old_jobs())
    await initialize_admin_orcids()

async def initialize_admin_orcids():
    try:
        async with AsyncSessionLocal() as session:
            # Define the list of admin ORCIDs
            admin_orcid_list = [
                '0000-0002-4762-3518',
                '0009-0007-0977-7798',  # Your ORCID
                '0009-0004-7542-9036',  # Additional admin ORCID
                # Add more admin ORCIDs as needed
            ]
            
            async with session.begin():
                # Get all existing admin ORCIDs
                result = await session.execute(select(AdminOrcid))
                admin_orcids = result.scalars().all()
                
                # Initialize if empty
                if not admin_orcids:
                    logging.info("No admin ORCIDs found, initializing...")
                    for orcid in admin_orcid_list:
                        session.add(AdminOrcid(orcid=orcid))
                else:
                    logging.info(f"Found {len(admin_orcids)} existing admin ORCIDs, checking for updates...")
                    
                    # Add any missing admin ORCIDs
                    existing_orcids = [admin.orcid for admin in admin_orcids]
                    for orcid in admin_orcid_list:
                        if orcid not in existing_orcids:
                            logging.info(f"Adding new admin ORCID: {orcid}")
                            session.add(AdminOrcid(orcid=orcid))

            # Start a new transaction for user role updates
            async with session.begin():
                # Update user roles for all admin ORCIDs
                for orcid in admin_orcid_list:
                    # Find the user with this ORCID
                    user_result = await session.execute(select(User).filter(User.orcid == orcid))
                    user = user_result.scalar_one_or_none()
                    
                    if user:
                        if user.role != UserRoleEnum.ADMIN.value:
                            logging.info(f"Updating user {user.full_name} (ORCID: {user.orcid}) to admin role")
                            user.role = UserRoleEnum.ADMIN.value
                        else:
                            logging.info(f"User {user.full_name} (ORCID: {user.orcid}) already has admin role")
                    else:
                        logging.info(f"User with ORCID {orcid} not found in users table (will be updated when they first log in)")
                
                logging.info("Admin roles updated successfully")
    except Exception as e:
        logging.error(f"Error initializing admin ORCIDs: {str(e)}", exc_info=True)
        raise

import os
print("Current Working Directory:", os.getcwd())

@app.get("/")
def read_root():
    return {"HaploSearch Database: v0.1.0"}

@app.get("/login")
def redirect_to_login():
    return RedirectResponse(url="/auth/login")

@app.get("/protected-route", response_model=UserResponse)
async def protected_route(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@app.get("/admin-route", response_model=UserResponse)
async def admin_route(admin_user: UserResponse = Depends(get_admin_user)):
    return admin_user

@app.get("/health")
async def health_check():
    """
    Health check endpoint for container health monitoring.
    Verifies database connectivity and critical services.
    """
    health_status = {
        "status": "healthy",
        "checks": {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # Check database connectivity
        async with AsyncSessionLocal() as session:
            await session.execute(select(1))
            health_status["checks"]["database"] = {
                "status": "connected",
                "error": None
            }
    except SQLAlchemyError as e:
        logging.error(f"Database health check failed: {str(e)}")
        health_status.update({
            "status": "unhealthy",
            "checks": {
                "database": {
                    "status": "disconnected",
                    "error": str(e)
                }
            }
        })
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )
    # Check temp directory access
    try:
        temp_dir = os.getenv('TEMP_UPLOAD_DIR', '/tmp/microhap')
        test_file = os.path.join(temp_dir, 'health_check.tmp')
        
        # Try to write to temp directory
        with open(test_file, 'w') as f:
            f.write('health check')
        
        # Clean up test file
        os.remove(test_file)
        
        health_status["checks"]["file_system"] = {
            "status": "writable",
            "error": None
        }
    except Exception as e:
        logging.error(f"File system health check failed: {str(e)}")
        health_status.update({
            "status": "unhealthy",
            "checks": {
                **health_status["checks"],
                "file_system": {
                    "status": "error",
                    "error": str(e)
                }
            }
        })
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
