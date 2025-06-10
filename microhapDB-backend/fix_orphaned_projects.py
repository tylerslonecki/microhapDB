#!/usr/bin/env python3
"""
Utility script to fix orphaned projects by associating them with programs
based on the database upload history.

This script should be run after the backend fix to ensure existing projects
are properly associated with programs.
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, insert
from src.database import AsyncSessionLocal
from src.models import Project, Program, DatabaseVersion, program_project_association

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fix_orphaned_projects():
    """
    Fix orphaned projects by associating them with programs based on database version descriptions.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Find all projects that are not associated with any program
            orphaned_projects_stmt = (
                select(Project)
                .outerjoin(program_project_association, Project.id == program_project_association.c.project_id)
                .where(program_project_association.c.project_id.is_(None))
            )
            
            result = await db.execute(orphaned_projects_stmt)
            orphaned_projects = result.scalars().all()
            
            if not orphaned_projects:
                logger.info("No orphaned projects found.")
                return
            
            logger.info(f"Found {len(orphaned_projects)} orphaned projects")
            
            for project in orphaned_projects:
                logger.info(f"Processing orphaned project: {project.name}")
                
                # Try to find a database version that mentions this project in its description
                version_stmt = select(DatabaseVersion).where(
                    DatabaseVersion.description.ilike(f"%{project.name}%")
                )
                
                result = await db.execute(version_stmt)
                matching_versions = result.scalars().all()
                
                if matching_versions:
                    # Use the program from the most recent matching version
                    latest_version = max(matching_versions, key=lambda v: v.created_at)
                    program_id = latest_version.program_id
                    
                    # Check if this association already exists
                    existing_assoc_stmt = select(program_project_association).where(
                        and_(
                            program_project_association.c.program_id == program_id,
                            program_project_association.c.project_id == project.id
                        )
                    )
                    existing_result = await db.execute(existing_assoc_stmt)
                    existing_assoc = existing_result.fetchone()
                    
                    if not existing_assoc:
                        # Create the association
                        await db.execute(
                            insert(program_project_association).values(
                                program_id=program_id,
                                project_id=project.id
                            )
                        )
                        
                        # Get program name for logging
                        program_stmt = select(Program).where(Program.id == program_id)
                        program_result = await db.execute(program_stmt)
                        program = program_result.scalar_one()
                        
                        logger.info(f"Associated project '{project.name}' with program '{program.name}'")
                    else:
                        logger.info(f"Association already exists for project '{project.name}'")
                else:
                    logger.warning(f"Could not find a suitable program for project '{project.name}'")
            
            await db.commit()
            logger.info("Successfully fixed orphaned projects")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error fixing orphaned projects: {str(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(fix_orphaned_projects()) 