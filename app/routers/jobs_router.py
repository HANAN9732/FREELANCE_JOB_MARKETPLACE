from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.core.dependencies import get_db, get_current_user , require_client ,require_freelancer
from app.core.logger import logger
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

    logger.info(f"Job created | job_id={new_job.id} | by user_id={current_user.id} | title={job_data.title}")

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

    logger.info(f"Job created | job_id={new_job.id} | by user_id={current_user.id} | title={job_data.title}")

    return new_job

@router.get(
    "/",
    response_model=list[JobResponse]
)
def get_all_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer)
):
    jobs = db.query(Job).filter(
        Job.is_deleted == False,
        Job.status == "open"
    ).all()

    return jobs  

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

    logger.info(f"Job updated | job_id={job.id} | by user_id={current_user.id} | fields={list(update_data.keys())}")

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

    logger.info(f"Job updated | job_id={job.id} | by user_id={current_user.id} | fields={list(update_data.keys())}")

    return job
from datetime import datetime

@router.delete("/{job_id}")
def delete_job(
    job_id: str,
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

    if job.client_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own jobs"
        )

    # Soft delete
    job.is_deleted = True

    # Close the job
    job.status = "closed"

    # Store deletion time
    job.deleted_at = datetime.utcnow()

    db.commit()

    logger.info(f"Job deleted | job_id={job.id} | by user_id={current_user.id}")

    return {
        "message": "Job deleted successfully",
        "deleted_at": job.deleted_at
    }
    
@router.post(
    "/{job_id}/submit-for-approval",
    response_model=JobResponse
)
def submit_job_for_approval(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer)
):
    """
    Freelancer marks their work as done. Moves the job to
    'pending_client_approval' — the client must approve before
    it's marked completed.
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.is_deleted == False
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.assigned_freelancer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only submit jobs assigned to you"
        )

    if job.status not in ("assigned", "in_progress"):
        raise HTTPException(
            status_code=400,
            detail=f"Job cannot be submitted for approval from status '{job.status}'"
        )

    job.status = "pending_client_approval"

    db.commit()
    db.refresh(job)

    logger.info(f"Job submitted for approval | job_id={job.id} | by freelancer_id={current_user.id}")

    return job


@router.post(
    "/{job_id}/approve-completion",
    response_model=JobResponse
)
def approve_job_completion(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client)
):
    """
    Client confirms the freelancer's submitted work. Only callable
    after the freelancer has hit /submit-for-approval. Moves the job
    to 'completed' — the point where reviews become unlocked.
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.is_deleted == False
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.client_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only approve completion on your own jobs"
        )

    if job.status != "pending_client_approval":
        raise HTTPException(
            status_code=400,
            detail="This job has not been submitted for approval yet"
        )

    job.status = "completed"

    db.commit()
    db.refresh(job)

    logger.info(f"Job completion approved | job_id={job.id} | by client_id={current_user.id}")

    return job