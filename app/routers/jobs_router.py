from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.core.dependencies import get_db, get_current_user , require_client
from app.models.user import User
from datetime import datetime


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)
@router.post(
    "",
    response_model=JobResponse,
    status_code=201
)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    new_job = Job(
        client_id=current_user.id,
        title=job_data.title,
        description=job_data.description,
        budget=job_data.budget,
        deadline=job_data.deadline,
        status="open"
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job

@router.post(
    "",
    response_model=JobResponse,
    status_code=201
)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client)
):

    new_job = Job(
        client_id=current_user.id,
        title=job_data.title,
        description=job_data.description,
        budget=job_data.budget,
        deadline=job_data.deadline,
        status="open"
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job

@router.get(
    "/{job_identifier}",
    response_model=JobResponse
)
def get_job(
    job_identifier: str,
    db: Session = Depends(get_db)
):

    job = db.query(Job).filter(
        Job.is_deleted == False,
        Job.id == job_identifier
    ).first()

    if not job:
        job = db.query(Job).filter(
            Job.is_deleted == False,
            Job.title == job_identifier
        ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return job

@router.put(
    "/{job_id}",
    response_model=JobResponse
)
def update_job(
    job_id: str,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client)
):

    job = db.query(Job).filter(
        Job.id == job_id
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    if str(job.client_id) != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail="You can only update your own jobs"
        )

    update_data = job_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return job

@router.put(
    "/{job_id}",
    response_model=JobResponse
)
def update_job(
    job_id: str,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client)
):

    job = db.query(Job).filter(
        Job.id == job_id
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    if str(job.client_id) != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail="You can only update your own jobs"
        )

    update_data = job_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return job

@router.delete("/{job_id}")
def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client)
):

    job = db.query(Job).filter(
        Job.id == job_id,
        Job.deleted_at.is_(None)
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    if job.client_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own jobs"
        )

    job.deleted_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Job deleted successfully"
    }
    