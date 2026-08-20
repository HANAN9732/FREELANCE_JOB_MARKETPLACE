from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_client
from app.core.logger import logger
from app.models.user import User
from app.models.job import Job
from app.models.skill import Skill
from app.models.job_skill import JobSkill
from app.schemas.job_skill import JobSkillResponse


router = APIRouter(
    prefix="/jobs",
    tags=["Job Skills"]
)

# Skills can't be added/removed once a job has reached one of these states
LOCKED_JOB_STATUSES = ("completed", "closed")


# Add a required skill to a job
@router.post(
    "/{job_id}/skills/{skill_id}",
    response_model=JobSkillResponse,
    status_code=status.HTTP_201_CREATED
)
def add_job_skill(
    job_id: str,
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client)
):

    # Check that the job exists and is active
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.is_deleted == False
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    # Make sure the logged-in client owns this job
    if job.client_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only add skills to your own jobs"
        )

    # Cannot modify skills once the job is completed or closed
    if job.status in LOCKED_JOB_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot add skills to a job that is '{job.status}'"
        )

    # Check that the skill exists
    skill = db.query(Skill).filter(
        Skill.id == skill_id,
        Skill.deleted_at.is_(None)
    ).first()

    if not skill:
        raise HTTPException(
            status_code=404,
            detail="Skill not found"
        )

    # Check for duplicate skill
    existing_skill = db.query(JobSkill).filter(
        JobSkill.job_id == job_id,
        JobSkill.skill_id == skill_id
    ).first()

    if existing_skill:
        raise HTTPException(
            status_code=400,
            detail="This skill is already required for this job"
        )

    job_skill = JobSkill(
        job_id=job_id,
        skill_id=skill_id
    )

    db.add(job_skill)
    db.commit()
    db.refresh(job_skill)

    logger.info(f"Job skill added | job_id={job_id} | skill_id={skill_id} | by user_id={current_user.id}")

    return job_skill


# Get all required skills for a job
@router.get(
    "/{job_id}/skills",
    response_model=list[JobSkillResponse]
)
def get_job_skills(
    job_id: str,
    db: Session = Depends(get_db)
):

    job = db.query(Job).filter(
        Job.id == job_id,
        Job.is_deleted == False
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    job_skills = db.query(JobSkill).filter(
        JobSkill.job_id == job_id
    ).all()

    return job_skills


# Remove a required skill from a job
@router.delete(
    "/{job_id}/skills/{skill_id}"
)
def remove_job_skill(
    job_id: str,
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client)
):

    job = db.query(Job).filter(
        Job.id == job_id,
        Job.is_deleted == False
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    # Only the owner of the job can remove its skills
    if job.client_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only remove skills from your own jobs"
        )

    # Cannot modify skills once the job is completed or closed
    if job.status in LOCKED_JOB_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot remove skills from a job that is '{job.status}'"
        )

    job_skill = db.query(JobSkill).filter(
        JobSkill.job_id == job_id,
        JobSkill.skill_id == skill_id
    ).first()

    if not job_skill:
        raise HTTPException(
            status_code=404,
            detail="Skill is not assigned to this job"
        )

    db.delete(job_skill)
    db.commit()

    logger.info(f"Job skill removed | job_id={job_id} | skill_id={skill_id} | by user_id={current_user.id}")

    return {
        "message": "Skill removed from job successfully"
    }