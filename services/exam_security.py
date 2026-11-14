
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from database import get_db
from models import TestAttempt, User
from services.auth import get_current_user


router = APIRouter(
    prefix="/student",
    tags=["Student Security"]
)


# 1. Common Security Check
def check_active_attempt(
    attempt_id: int,
    db: Session,
    current_user: User
):
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id,
        TestAttempt.student_id == current_user.id
    ).first()

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="Attempt not found"
        )

    if attempt.is_locked or attempt.status != "in_progress":
        raise HTTPException(
            status_code=403,
            detail="This test is locked or no longer active"
        )

    return attempt


# 2. Record Exam Warning
@router.post("/attempts/{attempt_id}/warning")
def record_exam_warning(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students allowed"
        )

    attempt = check_active_attempt(
        attempt_id, db, current_user
    )

    attempt.warning_count = (attempt.warning_count or 0) + 1

    if attempt.warning_count >= 3:
        attempt.is_locked = True
        attempt.status = "terminated"
        attempt.termination_reason = (
            "Maximum window switching limit exceeded"
        )

        db.commit()

        return {
            "message": "Test terminated due to repeated window switching",
            "warning_count": attempt.warning_count,
            "is_locked": True,
            "status": attempt.status
        }

    db.commit()

    return {
        "message": f"Warning {attempt.warning_count}: Do not leave the exam window",
        "warning_count": attempt.warning_count,
        "remaining_warnings": 3 - attempt.warning_count,
        "is_locked": False,
        "status": attempt.status
    }


# 3. Terminate Exam on Exit
@router.post("/attempts/{attempt_id}/exit")
def terminate_exam_on_exit(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students allowed"
        )

    attempt = check_active_attempt(
        attempt_id, db, current_user
    )

    attempt.is_locked = True
    attempt.status = "terminated"
    attempt.termination_reason = "Student exited the exam"

    db.commit()

    return {
        "message": "Test terminated because student exited the exam",
        "attempt_id": attempt.id,
        "status": attempt.status,
        "is_locked": attempt.is_locked
    }



@router.post("/attempts/{attempt_id}/heartbeat")
def update_exam_heartbeat(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Check student role
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students allowed"
        )

    # 2. Check whether exam attempt is active
    attempt = check_active_attempt(
        attempt_id,
        db,
        current_user
    )

    # 3. Update last heartbeat time
    attempt.last_heartbeat = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": "Heartbeat received successfully",
        "attempt_id": attempt.id,
        "last_heartbeat": attempt.last_heartbeat
    }

@router.post("/attempts/{attempt_id}/resume")
def resume_exam(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Check student role
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students allowed"
        )

    # 2. Verify existing attempt
    attempt = check_active_attempt(
        attempt_id,
        db,
        current_user
    )

    # 3. Update heartbeat after resuming
    attempt.last_heartbeat = datetime.now(timezone.utc)

    db.commit()
    db.refresh(attempt)

    return {
        "message": "Exam resumed successfully",
        "attempt_id": attempt.id,
        "test_id": attempt.test_id,
        "status": attempt.status,
        "last_heartbeat": attempt.last_heartbeat
    }
