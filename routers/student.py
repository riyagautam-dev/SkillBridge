
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, timedelta

from database import get_db
from models import (
    Test, Question, QuestionOption, User,
    TestAttempt, StudentAnswer, CodeSubmission, TestCase
)
from services.auth import get_current_user
from schemas import StudentAnswerSubmit, CodeSubmissionCreate
from judge0_service import run_code
from services.exam_security import check_active_attempt

router = APIRouter(prefix="/student", tags=["Student"])


# =====================================================
# TIMER AND AUTO SUBMIT HELPER FUNCTIONS
# =====================================================

def get_test_expiry(attempt, test):
    started_at = attempt.started_at

    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)

    return started_at + timedelta(minutes=test.duration_minutes)


def is_test_time_over(attempt, test):
    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    expires_at = get_test_expiry(attempt, test)

    return datetime.now(timezone.utc) >= expires_at


def finalize_test_attempt(attempt, db):
    # 1. Get all questions
    questions = db.query(Question).filter(
        Question.test_id == attempt.test_id
    ).all()

    # 2. Get saved MCQ answers
    answers = db.query(StudentAnswer).filter(
        StudentAnswer.attempt_id == attempt.id
    ).all()

    mcq_score = 0

    for answer in answers:
        if answer.is_correct:
            question = next(
                (q for q in questions if q.id == answer.question_id),
                None
            )

            if question:
                mcq_score += question.marks or 1

    # 3. Get coding submissions
    submissions = db.query(CodeSubmission).filter(
        CodeSubmission.attempt_id == attempt.id
    ).order_by(CodeSubmission.id).all()

    # Get latest submission of each question
    latest_submissions = {}

    for submission in submissions:
        latest_submissions[submission.question_id] = submission

    # 4. Calculate coding score
    coding_score = sum(
        submission.score or 0
        for submission in latest_submissions.values()
        if submission.status != "pending"
    )

    # 5. Calculate total marks
    total_marks = sum(
        q.marks if q.marks is not None else 1
        for q in questions
    )

    final_score = mcq_score + coding_score

    # 6. Update attempt
    attempt.score = final_score
    attempt.status = "submitted"
    attempt.submitted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(attempt)

    return {
        "message": "Test auto-submitted because time is over",
        "attempt_id": attempt.id,
        "total_questions": len(questions),
        "mcq_score": mcq_score,
        "coding_score": coding_score,
        "final_score": final_score,
        "total_marks": total_marks,
        "percentage": round(
            (final_score / total_marks) * 100, 2
        ) if total_marks > 0 else 0,
        "status": attempt.status
    }


# =====================================================
# 1. STUDENT AVAILABLE TESTS
# =====================================================

@router.get("/tests")
def get_available_tests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students allowed"
        )

    attempted_test_ids = db.query(
        TestAttempt.test_id
    ).filter(
        TestAttempt.student_id == current_user.id
    ).all()

    attempted_test_ids = [
        item[0] for item in attempted_test_ids
    ]

    tests = db.query(Test).filter(
        Test.is_active == True,
        ~Test.id.in_(attempted_test_ids)
    ).all()

    return [
        {
            "test_id": test.id,
            "title": test.title,
            "description": test.description,
            "duration_minutes": test.duration_minutes
        }
        for test in tests
    ]


# =====================================================
# 2. STUDENT GET TEST QUESTIONS
# =====================================================

@router.get("/tests/{test_id}/questions")
def get_student_questions(
    test_id: int,
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
        attempt_id,
        db,
        current_user
    )

    if attempt.test_id != test_id:
        raise HTTPException(
            status_code=403,
            detail="This attempt does not belong to this test"
        )

    test = db.query(Test).filter(
        Test.id == test_id,
        Test.is_active == True
    ).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    # Check timer
    if is_test_time_over(attempt, test):
        return finalize_test_attempt(attempt, db)

    questions = db.query(Question).filter(
        Question.test_id == test_id
    ).all()

    result = []

    for question in questions:
        options = db.query(QuestionOption).filter(
            QuestionOption.question_id == question.id
        ).all()

        result.append({
            "question_id": question.id,
            "title": question.title,
            "description": question.description,
            "question_type": question.question_type,
            "difficulty": question.difficulty,
            "options": [
                {
                    "option_id": option.id,
                    "option_text": option.option_text
                }
                for option in options
            ]
        })

    expires_at = get_test_expiry(attempt, test)

    remaining_seconds = max(
        0,
        int(
            (expires_at - datetime.now(timezone.utc)).total_seconds()
        )
    )

    return {
        "test_id": test.id,
        "test_title": test.title,
        "duration_minutes": test.duration_minutes,
        "remaining_seconds": remaining_seconds,
        "total_questions": len(result),
        "questions": result
    }


# =====================================================
# 3. START TEST
# =====================================================

@router.post("/tests/{test_id}/start")
def start_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students allowed"
        )

    test = db.query(Test).filter(
        Test.id == test_id,
        Test.is_active == True
    ).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found or inactive"
        )

    existing_attempt = db.query(TestAttempt).filter(
        TestAttempt.student_id == current_user.id,
        TestAttempt.test_id == test_id
    ).first()

    if existing_attempt:

        if existing_attempt.is_locked:
            raise HTTPException(
                status_code=403,
                detail="You are permanently locked out of this test"
            )

        if existing_attempt.status == "submitted":
            raise HTTPException(
                status_code=403,
                detail="You have already submitted this test"
            )

        raise HTTPException(
            status_code=403,
            detail="You already have an attempt for this test. New attempt is not allowed."
        )

    attempt = TestAttempt(
        student_id=current_user.id,
        test_id=test_id
    )

    db.add(attempt)

    try:
        db.commit()
        db.refresh(attempt)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=403,
            detail="You already have an attempt for this test. New attempt is not allowed."
        )

    expires_at = get_test_expiry(attempt, test)

    remaining_seconds = max(
        0,
        int(
            (expires_at - datetime.now(timezone.utc)).total_seconds()
        )
    )

    return {
        "message": "Test started successfully",
        "attempt_id": attempt.id,
        "test_id": attempt.test_id,
        "status": attempt.status,
        "started_at": attempt.started_at,
        "duration_minutes": test.duration_minutes,
        "expires_at": expires_at,
        "remaining_seconds": remaining_seconds,
        "warning_count": attempt.warning_count,
        "is_locked": attempt.is_locked
    }


# =====================================================
# 4. SAVE MCQ ANSWER
# =====================================================

@router.post("/attempts/{attempt_id}/answer")
def submit_answer(
    attempt_id: int,
    data: StudentAnswerSubmit,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students allowed"
        )

    attempt = check_active_attempt(
        attempt_id,
        db,
        current_user
    )

    # Check test timer
    test = db.query(Test).filter(
        Test.id == attempt.test_id
    ).first()

    if is_test_time_over(attempt, test):
        return finalize_test_attempt(attempt, db)

    # Check question belongs to this test
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.test_id == attempt.test_id
    ).first()

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Question not found in this test"
        )

    # Check selected option
    option = db.query(QuestionOption).filter(
        QuestionOption.id == data.selected_option_id,
        QuestionOption.question_id == question_id
    ).first()

    if not option:
        raise HTTPException(
            status_code=400,
            detail="Invalid option"
        )

    # Save or update answer
    answer = db.query(StudentAnswer).filter(
        StudentAnswer.attempt_id == attempt_id,
        StudentAnswer.question_id == question_id
    ).first()

    if answer:
        answer.selected_option_id = option.id
        answer.is_correct = option.is_correct

    else:
        answer = StudentAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option_id=option.id,
            is_correct=option.is_correct
        )

        db.add(answer)

    db.commit()

    return {
        "message": "Answer saved successfully",
        "question_id": question_id,
        "selected_option_id": option.id
    }


# =====================================================
# 5. SUBMIT TEST
# =====================================================

@router.post("/attempts/{attempt_id}/submit")
def submit_test(
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
        attempt_id,
        db,
        current_user
    )

    # Check test timer
    test = db.query(Test).filter(
        Test.id == attempt.test_id
    ).first()

    if is_test_time_over(attempt, test):
        return finalize_test_attempt(attempt, db)

    # Get all questions
    questions = db.query(Question).filter(
        Question.test_id == attempt.test_id
    ).all()

    mcq_questions = [
        q for q in questions if q.question_type != "coding"
    ]

    coding_questions = [
        q for q in questions if q.question_type == "coding"
    ]

    # Get MCQ answers
    answers = db.query(StudentAnswer).filter(
        StudentAnswer.attempt_id == attempt_id
    ).all()

    answered_question_ids = {
        answer.question_id for answer in answers
    }

    if len(answered_question_ids) < len(mcq_questions):
        raise HTTPException(
            status_code=400,
            detail="Please answer all MCQ questions"
        )

    # Calculate MCQ score
    mcq_score = 0

    for answer in answers:
        if answer.is_correct:
            question = next(
                (q for q in mcq_questions if q.id == answer.question_id),
                None
            )

            if question:
                mcq_score += question.marks or 1

    # Get coding submissions
    coding_submissions = db.query(CodeSubmission).filter(
        CodeSubmission.attempt_id == attempt_id
    ).order_by(CodeSubmission.id).all()

    latest_submissions = {}

    for submission in coding_submissions:
        latest_submissions[submission.question_id] = submission

    # Check all coding questions submitted
    for question in coding_questions:
        submission = latest_submissions.get(question.id)

        if not submission:
            raise HTTPException(
                status_code=400,
                detail=f"Please submit coding question ID {question.id}"
            )

        if submission.status == "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Coding question ID {question.id} is still processing"
            )

    # Calculate coding score
    coding_score = sum(
        submission.score or 0
        for submission in latest_submissions.values()
    )

    # Calculate total marks
    total_marks = sum(
        q.marks if q.marks is not None else 1
        for q in questions
    )

    final_score = mcq_score + coding_score

    # Submit attempt
    attempt.score = final_score
    attempt.status = "submitted"
    attempt.submitted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(attempt)

    return {
        "message": "Test submitted successfully",
        "attempt_id": attempt.id,
        "total_questions": len(questions),
        "mcq_score": mcq_score,
        "coding_score": coding_score,
        "final_score": final_score,
        "total_marks": total_marks,
        "percentage": round(
            (final_score / total_marks) * 100, 2
        ) if total_marks > 0 else 0,
        "status": attempt.status
    }


# =====================================================
# 6. STUDENT RESULTS
# =====================================================

@router.get("/results")
def get_student_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students allowed"
        )

    attempts = db.query(TestAttempt).filter(
        TestAttempt.student_id == current_user.id,
        TestAttempt.status == "submitted"
    ).all()

    results = []

    for attempt in attempts:

        test = db.query(Test).filter(
            Test.id == attempt.test_id
        ).first()

        questions = db.query(Question).filter(
            Question.test_id == attempt.test_id
        ).all()

        mcq_questions = [
            q for q in questions if q.question_type != "coding"
        ]

        coding_questions = [
            q for q in questions if q.question_type == "coding"
        ]

        answers = db.query(StudentAnswer).filter(
            StudentAnswer.attempt_id == attempt.id
        ).all()

        correct_answers = sum(
            1 for answer in answers if answer.is_correct
        )

        wrong_answers = sum(
            1 for answer in answers if not answer.is_correct
        )

        mcq_score = sum(
            (q.marks if q.marks is not None else 1)
            for q in mcq_questions
            if any(
                a.question_id == q.id and a.is_correct
                for a in answers
            )
        )

        submissions = db.query(CodeSubmission).filter(
            CodeSubmission.attempt_id == attempt.id
        ).order_by(CodeSubmission.id).all()

        latest_submissions = {}

        for submission in submissions:
            latest_submissions[submission.question_id] = submission

        coding_score = sum(
    (latest_submissions[q.id].score or 0)
    for q in coding_questions
    if (
        q.id in latest_submissions
        and latest_submissions[q.id].status != "pending"
    )
)

        total_marks = sum(
            q.marks if q.marks is not None else 1
            for q in questions
        )

        final_score= attempt.score or 0

        percentage = (
            (final_score / total_marks) * 100
            if total_marks > 0 else 0
        )

        results.append({
            "attempt_id": attempt.id,
            "test_id": attempt.test_id,
            "test_title": test.title if test else "Unknown Test",
            "total_questions": len(questions),
            "mcq_questions": len(mcq_questions),
            "coding_questions": len(coding_questions),
            "answered_mcq": len(answers),
            "correct_answers": correct_answers,
            "wrong_answers": wrong_answers,
            "mcq_score": mcq_score,
            "coding_score": coding_score,
            "final_score": attempt.score,
            "total_marks": total_marks,
            "percentage": round(percentage, 2),
            "submitted_at": attempt.submitted_at
        })

    return {
        "total_tests": len(results),
        "results": results
    }


# =====================================================
# 7. GET CODING QUESTIONS
# =====================================================

@router.get("/tests/{test_id}/coding-questions")
def get_coding_questions(
    test_id: int,
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
        attempt_id,
        db,
        current_user
    )

    if attempt.test_id != test_id:
        raise HTTPException(
            status_code=403,
            detail="This attempt does not belong to this test"
        )

    test = db.query(Test).filter(
        Test.id == test_id,
        Test.is_active == True
    ).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    # Check timer
    if is_test_time_over(attempt, test):
        return finalize_test_attempt(attempt, db)

    questions = db.query(Question).filter(
        Question.test_id == test_id,
        Question.question_type == "coding"
    ).all()

    return [
        {
            "question_id": q.id,
            "title": q.title,
            "description": q.description,
            "difficulty": q.difficulty,
            "allowed_languages": q.allowed_languages,
            "marks": q.marks
        }
        for q in questions
    ]


# =====================================================
# 8. SUBMIT CODING ANSWER
# =====================================================

@router.post("/attempts/{attempt_id}/questions/{question_id}/submit-code")
def submit_code(
    attempt_id: int,
    question_id: int,
    data: CodeSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Student role check
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students allowed"
        )

    # Active attempt check
    attempt = check_active_attempt(
        attempt_id,
        db,
        current_user
    )
    
    # Check test timer
    test = db.query(Test).filter(
        Test.id == attempt.test_id
    ).first()

    if is_test_time_over(attempt, test):
        return finalize_test_attempt(attempt, db)

    # Check coding question
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.test_id == attempt.test_id,
        Question.question_type == "coding"
    ).first()

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Coding question not found"
        )

    # Check allowed language
    if data.programming_language not in (
        question.allowed_languages or []
    ):
        raise HTTPException(
            status_code=400,
            detail="This programming language is not allowed"
        )

    # Get test cases
    test_cases = db.query(TestCase).filter(
        TestCase.question_id == question_id
    ).order_by(TestCase.id).all()

    if not test_cases:
        raise HTTPException(
            status_code=400,
            detail="No test cases available for this question"
        )

    passed_cases = 0
    earned_case_marks = 0

    total_case_marks = sum(
        tc.marks for tc in test_cases
    )

    visible_results = []
    final_status = "accepted"

    # Run code against test cases
    for tc in test_cases:

        result = run_code(
            source_code=data.source_code,
            language=data.programming_language,
            input_data=tc.input_data or ""
        )

        status_id = result["status"]["id"]

        if status_id != 3:

            if status_id == 6:
                final_status = "compilation_error"

            elif status_id == 5:
                final_status = "time_limit_exceeded"

            elif status_id in [1, 2]:
                final_status = "pending"

            else:
                final_status = "runtime_error"

            if not tc.is_hidden:
                visible_results.append({
                    "test_case_id": tc.id,
                    "passed": False,
                    "error": (
                        result.get("stderr")
                        or result["status"]["description"]
                    )
                })

            break

        actual_output = (
            result.get("stdout") or ""
        ).strip()

        expected_output = (
            tc.expected_output or ""
        ).strip()

        passed = actual_output == expected_output

        if passed:
            passed_cases += 1
            earned_case_marks += tc.marks

        else:
            final_status = "wrong_answer"

        if not tc.is_hidden:
            visible_results.append({
                "test_case_id": tc.id,
                "passed": passed,
                "your_output": actual_output
            })

    # Calculate coding score
    if final_status == "accepted" and total_case_marks > 0:
        score = question.marks

    elif total_case_marks > 0:
        score = round(
            question.marks * earned_case_marks / total_case_marks
        )

    else:
        score = 0

    # Save code submission
    submission = CodeSubmission(
        attempt_id=attempt_id,
        question_id=question_id,
        programming_language=data.programming_language,
        source_code=data.source_code,
        status=final_status,
        score=score
    )

    db.add(submission)
    db.commit()
    db.refresh(submission)

    return {
        "message": "Code evaluated successfully",
        "submission_id": submission.id,
        "question_id": question_id,
        "status": final_status,
        "score": score,
        "total_marks": question.marks,
        "passed_test_cases": passed_cases,
        "total_test_cases": len(test_cases),
        "visible_test_results": visible_results
    }


# =====================================================
# 9. STUDENT DASHBOARD
# =====================================================


@router.get("/dashboard")
def student_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Student role check
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students allowed"
        )

    # 2. Get all student attempts
    attempts = db.query(TestAttempt).filter(
        TestAttempt.student_id == current_user.id
    ).all()

    # 3. Separate submitted attempts
    submitted_attempts = [
        a for a in attempts if a.status == "submitted"
    ]

    # 4. Get attempted test IDs
    attempted_test_ids = [
        a.test_id for a in attempts
    ]

    # 5. Get only active tests not attempted by student
    active_tests_query = db.query(Test).filter(
        Test.is_active == True
    )

    if attempted_test_ids:
        active_tests_query = active_tests_query.filter(
            ~Test.id.in_(attempted_test_ids)
        )

    active_tests = active_tests_query.all()

    # 6. Basic statistics
    total_attempts = len(attempts)

    unique_tests_attempted = len(set(
        attempt.test_id for attempt in attempts
    ))

    completed_tests = len(submitted_attempts)

    in_progress_tests = sum(
        1 for a in attempts if a.status == "in_progress"
    )

    total_mcq_score = 0
    total_coding_score = 0
    total_marks = 0
    total_score = 0

    # 7. Calculate performance
    for attempt in submitted_attempts:

        questions = db.query(Question).filter(
            Question.test_id == attempt.test_id
        ).all()

        mcq_questions = [
            q for q in questions
            if q.question_type != "coding"
        ]

        coding_questions = [
            q for q in questions
            if q.question_type == "coding"
        ]

        answers = db.query(StudentAnswer).filter(
            StudentAnswer.attempt_id == attempt.id
        ).all()

        # Calculate MCQ score
        mcq_score = sum(
            (q.marks if q.marks is not None else 1)
            for q in mcq_questions
            if any(
                a.question_id == q.id and a.is_correct
                for a in answers
            )
        )

        # Get coding submissions
        submissions = db.query(CodeSubmission).filter(
            CodeSubmission.attempt_id == attempt.id
        ).order_by(CodeSubmission.id).all()

        latest_submissions = {}

        for submission in submissions:
            latest_submissions[submission.question_id] = submission

        # Calculate coding score (ignore pending submissions)
        coding_score = sum(
            (latest_submissions[q.id].score or 0)
            for q in coding_questions
            if (
                q.id in latest_submissions
                and latest_submissions[q.id].status != "pending"
            )
        )

        # Calculate total marks
        attempt_total_marks = sum(
            q.marks if q.marks is not None else 1
            for q in questions
        )

        total_mcq_score += mcq_score
        total_coding_score += coding_score
        total_marks += attempt_total_marks
        total_score += attempt.score or 0

    # 8. Calculate overall percentage
    percentage = (
        (total_score / total_marks) * 100
        if total_marks > 0 else 0
    )

    # 9. Get recent attempts
    recent_attempts = []

    for attempt in sorted(
        attempts,
        key=lambda a: a.started_at or datetime.min.replace(
            tzinfo=timezone.utc
        ),
        reverse=True
    )[:5]:

        test = db.query(Test).filter(
            Test.id == attempt.test_id
        ).first()

        recent_attempts.append({
            "attempt_id": attempt.id,
            "test_id": attempt.test_id,
            "test_title": test.title if test else "Unknown Test",
            "status": attempt.status,
            "score": attempt.score,
            "started_at": attempt.started_at,
            "submitted_at": attempt.submitted_at
        })

    # 10. Final dashboard response
    return {
        "student": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email
        },

        "statistics": {
            "total_available_tests": len(active_tests),
            "total_attempts": total_attempts,
            "completed_tests": completed_tests,
            "in_progress_tests": in_progress_tests,
            "unique_tests_attempted": unique_tests_attempted
        },

        "performance": {
            "mcq_score": total_mcq_score,
            "coding_score": total_coding_score,
            "total_score": total_score,
            "total_marks": total_marks,
            "percentage": round(percentage, 2)
        },

        "available_tests": [
            {
                "test_id": test.id,
                "title": test.title,
                "description": test.description,
                "duration_minutes": test.duration_minutes
            }
            for test in active_tests
        ],

        "recent_attempts": recent_attempts
    }


@router.get("/attempts/active")
def get_active_attempt(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students allowed"
        )

    attempt = db.query(TestAttempt).filter(
        TestAttempt.student_id == current_user.id,
        TestAttempt.status == "in_progress",
        TestAttempt.is_locked == False
    ).first()

    if not attempt:
        return {
            "message": "No active test attempt found",
            "attempt": None
        }

    test = db.query(Test).filter(
        Test.id == attempt.test_id
    ).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    if is_test_time_over(attempt, test):
        result = finalize_test_attempt(attempt, db)

        return {
            "message": "Test time is over",
            "attempt": None,
            "result": result
        }

    started_at = attempt.started_at

    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)

    expires_at = started_at + timedelta(
        minutes=test.duration_minutes
    )

    remaining_seconds = max(
        0,
        int(
            (expires_at - datetime.now(timezone.utc)).total_seconds()
        )
    )

    return {
        "message": "Active attempt found",
        "attempt": {
            "attempt_id": attempt.id,
            "test_id": attempt.test_id,
            "test_title": test.title,
            "status": attempt.status,
            "started_at": started_at,
            "expires_at": expires_at,
            "remaining_seconds": remaining_seconds,
            "warning_count": attempt.warning_count,
            "is_locked": attempt.is_locked
        }
    }