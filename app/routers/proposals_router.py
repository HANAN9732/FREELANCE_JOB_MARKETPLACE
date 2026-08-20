import os
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    status,
)
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    get_current_user,
    require_freelancer,
    require_client,
)
from app.core.logger import logger

from app.models.user import User
from app.models.job import Job
from app.models.proposal import Proposal

from app.schemas.proposal import ProposalResponse

from app.services.notification_service import create_notification

router = APIRouter(
    prefix="/proposals",
    tags=["Proposals"]
)

BASE_DIR = Path(__file__).resolve().parents[2]

UPLOAD_DIR = BASE_DIR / "uploads" / "proposals"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post(
    "/jobs/{job_id}",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_proposal(
    job_id: str,

    bid_amount: float = Form(...),

    delivery_time_days: int = Form(...),

    cover_letter: UploadFile = File(...),

    db: Session = Depends(get_db),

    current_user: User = Depends(require_freelancer)
):

    # -----------------------------------
    # 1. Check job
    # -----------------------------------

    job = db.query(Job).filter(
        Job.id == job_id,
        Job.is_deleted == False
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    # -----------------------------------
    # 2. Check job status
    # -----------------------------------

    if job.status != "open":
        raise HTTPException(
            status_code=400,
            detail="You cannot submit a proposal to a closed job"
        )

    # -----------------------------------
    # 3. Freelancer cannot apply
    #    to their own job
    # -----------------------------------

    if job.client_id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot submit a proposal to your own job"
        )

    # -----------------------------------
    # 4. Validate bid
    # -----------------------------------

    if bid_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Bid amount must be greater than 0"
        )

    # -----------------------------------
    # 5. Validate delivery time
    # -----------------------------------

    if delivery_time_days <= 0:
        raise HTTPException(
            status_code=400,
            detail="Delivery time must be greater than 0 days"
        )

    # -----------------------------------
    # 6. Check duplicate proposal
    # -----------------------------------

    existing_proposal = db.query(Proposal).filter(
        Proposal.job_id == job_id,
        Proposal.freelancer_id == current_user.id
    ).first()

    if existing_proposal:
        raise HTTPException(
            status_code=409,
            detail="You have already submitted a proposal for this job"
        )

    # -----------------------------------
    # 7. Validate PDF
    # -----------------------------------

    if cover_letter.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Cover letter must be a PDF file"
        )

    # -----------------------------------
    # 8. Validate filename
    # -----------------------------------

    if not cover_letter.filename:
        raise HTTPException(
            status_code=400,
            detail="Cover letter filename is required"
        )

    if not cover_letter.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Cover letter must have a .pdf extension"
        )

    # -----------------------------------
    # 9. Create upload directory
    # -----------------------------------

    upload_directory = UPLOAD_DIR

    upload_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------
    # 10. Generate freelancer-based filename
    # -----------------------------------

    # Get freelancer name
    freelancer_name = current_user.name.strip()

    # Replace characters that are unsafe
    # for Windows filenames
    safe_name = "".join(
        character
        for character in freelancer_name
        if character.isalnum() or character in (" ", "_", "-")
    ).strip()

    # Default name if somehow the user has no valid name
    if not safe_name:
        safe_name = "freelancer"

    base_file_name = f"{safe_name} proposal"
    file_name = f"{base_file_name}.pdf"

    file_path = upload_directory / file_name

    # -----------------------------------
    # Prevent overwriting existing files
    # -----------------------------------

    counter = 2

    while file_path.exists():

        file_name = f"{base_file_name}_{counter}.pdf"

        file_path = upload_directory / file_name

        counter += 1

    # -----------------------------------
    # 11. Save PDF
    # -----------------------------------

    try:

        file_content = await cover_letter.read()

    except Exception:

        logger.error(f"Failed to read uploaded cover letter | job_id={job_id} | by user_id={current_user.id}")

        raise HTTPException(
            status_code=500,
            detail="Unable to read uploaded file"
        )

    with open(file_path, "wb") as file:
        file.write(file_content)

    # -----------------------------------
    # 12. Create proposal
    # -----------------------------------

    proposal = Proposal(
        job_id=job_id,
        freelancer_id=current_user.id,
        bid_amount=bid_amount,
        cover_letter_path=str(file_path),
        delivery_time_days=delivery_time_days,
        status="pending"
    )

    db.add(proposal)

    try:

        db.commit()
        db.refresh(proposal)

    except IntegrityError:

        db.rollback()

        # Remove uploaded file if
        # database insertion failed

        if file_path.exists():
            file_path.unlink()

        logger.warning(f"Proposal creation failed (duplicate) | job_id={job_id} | by user_id={current_user.id}")

        raise HTTPException(
            status_code=409,
            detail="You have already submitted a proposal for this job"
        )

    # -----------------------------------
    # 13. Notify the client (job owner)
    #     that a new proposal came in
    # -----------------------------------
    #
    # Done AFTER commit + refresh, so
    # proposal.id is guaranteed to be
    # populated (it's DB-generated, not
    # set on the Python side).

    create_notification(
        db=db,
        user_id=job.client_id,
        type="new_proposal",
        reference_id=proposal.id,
        payload={
            "message": f"{current_user.name} sent a proposal to your job '{job.title}'",
            "job_id": job.id,
            "proposal_id": proposal.id,
            "freelancer_id": current_user.id,
        }
    )

    db.commit()

    logger.info(f"Proposal created | proposal_id={proposal.id} | job_id={job.id} | by freelancer_id={current_user.id} | bid_amount={bid_amount}")

    return proposal

@router.get(
    "/my",
    response_model=list[ProposalResponse]
)
def get_my_proposals(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer)
):
    proposals = db.query(Proposal).filter(
        Proposal.freelancer_id == current_user.id,
        Proposal.deleted_at.is_(None)
    ).all()

    return proposals
@router.get(
    "/jobs/{job_id}",
    response_model=list[ProposalResponse]
)
def get_job_proposals(
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

    # Make sure this is the client's job
    if job.client_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only view proposals for your own jobs"
        )

    proposals = db.query(Proposal).filter(
        Proposal.job_id == job_id,
        Proposal.deleted_at.is_(None)
    ).all()

    return proposals   

@router.get(
    "/{proposal_id}",
    response_model=ProposalResponse
)
def get_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    proposal = db.query(Proposal).filter(
        Proposal.id == proposal_id,
        Proposal.deleted_at.is_(None)
    ).first()

    if not proposal:
        raise HTTPException(
            status_code=404,
            detail="Proposal not found"
        )

    # Freelancer who created the proposal
    if proposal.freelancer_id == current_user.id:
        return proposal

    # Client who owns the job
    job = db.query(Job).filter(
        Job.id == proposal.job_id
    ).first()

    if job and job.client_id == current_user.id:
        return proposal

    raise HTTPException(
        status_code=403,
        detail="You are not allowed to view this proposal"
    )
@router.delete(
    "/{proposal_id}"
)
def withdraw_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_freelancer)
):

    proposal = db.query(Proposal).filter(
        Proposal.id == proposal_id,
        Proposal.deleted_at.is_(None)
    ).first()

    if not proposal:
        raise HTTPException(
            status_code=404,
            detail="Proposal not found"
        )

    # Only the freelancer who created it
    # can withdraw it
    if proposal.freelancer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only withdraw your own proposal"
        )

    # Only pending proposals can be withdrawn
    if proposal.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending proposals can be withdrawn"
        )

    proposal.status = "withdrawn"
    proposal.deleted_at = datetime.utcnow()

    db.commit()

    logger.info(f"Proposal withdrawn | proposal_id={proposal.id} | by freelancer_id={current_user.id}")

    return {
        "message": "Proposal withdrawn successfully"
    }

@router.patch(
    "/{proposal_id}/accept",
    response_model=ProposalResponse
)
def accept_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client)
):

    proposal = db.query(Proposal).filter(
        Proposal.id == proposal_id,
        Proposal.deleted_at.is_(None)
    ).first()

    if not proposal:
        raise HTTPException(
            status_code=404,
            detail="Proposal not found"
        )

    job = db.query(Job).filter(
        Job.id == proposal.job_id,
        Job.is_deleted == False
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    # Only job owner can accept
    if job.client_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only accept proposals for your own jobs"
        )

    # Job must still be open
    if job.status != "open":
        raise HTTPException(
            status_code=400,
            detail="This job is no longer open"
        )

    # Proposal must still be pending
    if proposal.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending proposals can be accepted"
        )

    # -----------------------------------
    # Fetch the OTHER pending proposals
    # for this job BEFORE we bulk-reject
    # them, so we still have their
    # freelancer_id available to notify.
    # -----------------------------------

    other_pending_proposals = db.query(Proposal).filter(
        Proposal.job_id == proposal.job_id,
        Proposal.id != proposal.id,
        Proposal.status == "pending",
        Proposal.deleted_at.is_(None)
    ).all()

    # Accept selected proposal
    proposal.status = "accepted"

    # Assign freelancer to job
    job.assigned_freelancer_id = proposal.freelancer_id

    # Close job to new proposals
    job.status = "assigned"

    # Reject all other pending proposals
    db.query(Proposal).filter(
        Proposal.job_id == proposal.job_id,
        Proposal.id != proposal.id,
        Proposal.status == "pending",
        Proposal.deleted_at.is_(None)
    ).update(
        {
            Proposal.status: "rejected"
        },
        synchronize_session=False
    )

    # -----------------------------------
    # Notify the accepted freelancer
    # -----------------------------------

    create_notification(
        db=db,
        user_id=proposal.freelancer_id,
        type="proposal_accepted",
        reference_id=proposal.id,
        payload={
            "message": f"Your proposal for '{job.title}' was accepted",
            "job_id": job.id,
            "proposal_id": proposal.id,
        }
    )

    # -----------------------------------
    # Notify every freelancer who just
    # got auto-rejected because someone
    # else was accepted
    # -----------------------------------

    for other_proposal in other_pending_proposals:
        create_notification(
            db=db,
            user_id=other_proposal.freelancer_id,
            type="proposal_rejected",
            reference_id=other_proposal.id,
            payload={
                "message": f"Your proposal for '{job.title}' was not selected",
                "job_id": job.id,
                "proposal_id": other_proposal.id,
            }
        )

    db.commit()
    db.refresh(proposal)

    logger.info(f"Proposal accepted | proposal_id={proposal.id} | job_id={job.id} | by client_id={current_user.id} | freelancer_id={proposal.freelancer_id} | auto_rejected_count={len(other_pending_proposals)}")

    return proposal 

@router.patch(
    "/{proposal_id}/reject",
    response_model=ProposalResponse
)
def reject_proposal(
    proposal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_client)
):

    proposal = db.query(Proposal).filter(
        Proposal.id == proposal_id,
        Proposal.deleted_at.is_(None)
    ).first()

    if not proposal:
        raise HTTPException(
            status_code=404,
            detail="Proposal not found"
        )

    job = db.query(Job).filter(
        Job.id == proposal.job_id,
        Job.is_deleted == False
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    # Only job owner can reject
    if job.client_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only reject proposals for your own jobs"
        )

    # Only pending proposals can be rejected
    if proposal.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending proposals can be rejected"
        )

    proposal.status = "rejected"

    # -----------------------------------
    # Notify the freelancer their
    # proposal was rejected
    # -----------------------------------

    create_notification(
        db=db,
        user_id=proposal.freelancer_id,
        type="proposal_rejected",
        reference_id=proposal.id,
        payload={
            "message": f"Your proposal for '{job.title}' was rejected",
            "job_id": job.id,
            "proposal_id": proposal.id,
        }
    )

    db.commit()
    db.refresh(proposal)

    logger.info(f"Proposal rejected | proposal_id={proposal.id} | job_id={job.id} | by client_id={current_user.id}")

    return proposal