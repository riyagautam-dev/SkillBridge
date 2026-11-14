
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Test, User, Question, QuestionOption,TestCase,TestAttempt,StudentAnswer,CodeSubmission
from schemas import (
    TestCreate,
    QuestionCreate,
    QuestionOptionCreate,
    AIQuestionsApprove,
    CodingQuestionCreate,
    TestCaseCreate
)
from services.auth import require_teacher
from ai_service import generate_questions


router = APIRouter(
    prefix="/teacher",
    tags=["Teacher"]
)


# 1. Create Test
@router.post("/tests", status_code=201)
def create_test(
    test_data: TestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    new_test = Test(
        title=test_data.title,
        description=test_data.description,
        duration_minutes=test_data.duration_minutes,
        teacher_id=current_user.id
    )

    db.add(new_test)
    db.commit()
    db.refresh(new_test)

    return {
        "message": "Test created successfully",
        "test_id": new_test.id,
        "title": new_test.title,
        "description": new_test.description,
        "duration_minutes": new_test.duration_minutes,
        "teacher_id": new_test.teacher_id
    }


# 2. Get Teacher Tests
@router.get("/tests")
def get_teacher_tests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    tests = db.query(Test).filter(
        Test.teacher_id == current_user.id
    ).all()

    return [
        {
            "test_id": test.id,
            "title": test.title,
            "description": test.description,
            "is_active": test.is_active
        }
        for test in tests
    ]


# 3. Delete Test

@router.delete("/tests/{test_id}")
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    test = db.query(Test).filter(
        Test.id == test_id,
        Test.teacher_id == current_user.id
    ).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    existing_attempts = db.query(TestAttempt).filter(
        TestAttempt.test_id == test_id
    ).count()

    if existing_attempts > 0:
        raise HTTPException(
            status_code=400,
            detail="This test cannot be deleted because students have already attempted it."
        )

    question_ids = [
        q.id for q in db.query(Question).filter(
            Question.test_id == test_id
        ).all()
    ]

    if question_ids:
        db.query(TestCase).filter(
            TestCase.question_id.in_(question_ids)
        ).delete(synchronize_session=False)

        db.query(QuestionOption).filter(
            QuestionOption.question_id.in_(question_ids)
        ).delete(synchronize_session=False)

        db.query(Question).filter(
            Question.id.in_(question_ids)
        ).delete(synchronize_session=False)

    db.delete(test)
    db.commit()

    return {
        "message": "Test deleted successfully"
    }



# 4. Update Test

@router.put("/tests/{test_id}")
def update_test(
    test_id: int,
    test_data: TestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    test = db.query(Test).filter(
        Test.id == test_id,
        Test.teacher_id == current_user.id
    ).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    test.title = test_data.title
    test.description = test_data.description
    test.duration_minutes = test_data.duration_minutes

    db.commit()
    db.refresh(test)

    return {
        "message": "Test updated successfully",
        "test_id": test.id,
        "title": test.title,
        "description": test.description,
        "duration_minutes": test.duration_minutes
    }

# 5. Create Question
@router.post("/tests/{test_id}/questions", status_code=201)
def create_question(
    test_id: int,
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    test = db.query(Test).filter(
        Test.id == test_id,
        Test.teacher_id == current_user.id
    ).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    new_question = Question(
        test_id=test_id,
        title=question_data.title,
        description=question_data.description,
        question_type=question_data.question_type,
        difficulty=question_data.difficulty
    )

    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    return {
        "message": "Question created successfully",
        "question_id": new_question.id,
        "test_id": new_question.test_id,
        "title": new_question.title,
        "question_type": new_question.question_type,
        "difficulty": new_question.difficulty
    }


# 6. Add Question Options
@router.post("/questions/{question_id}/options", status_code=201)
def add_question_options(
    question_id: int,
    option_data: QuestionOptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    question = (
        db.query(Question)
        .join(Test, Question.test_id == Test.id)
        .filter(
            Question.id == question_id,
            Test.teacher_id == current_user.id
        )
        .first()
    )

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Question not found"
        )

    if question.question_type != "mcq":
        raise HTTPException(
            status_code=400,
            detail="Options can only be added to MCQ questions"
        )

    existing_options = db.query(QuestionOption).filter(
        QuestionOption.question_id == question_id
    ).count()

    if existing_options > 0:
        raise HTTPException(
            status_code=400,
            detail="Options already exist for this question"
        )

    for index, option_text in enumerate(
        option_data.options, start=1
    ):
        new_option = QuestionOption(
            question_id=question_id,
            option_text=option_text,
            is_correct=(index == option_data.correct_option)
        )
        db.add(new_option)

    db.commit()

    return {
        "message": "Options added successfully",
        "question_id": question_id,
        "total_options": len(option_data.options)
    }


# 7. AI Generate Questions
@router.post("/ai/generate")
def generate_ai_questions(
    topic: str,
    mcq_count: int = 5,
    current_user: User = Depends(require_teacher)
):
    if not topic.strip():
        raise HTTPException(
            status_code=400,
            detail="Topic cannot be empty"
        )

    if mcq_count < 1 or mcq_count > 20:
        raise HTTPException(
            status_code=400,
            detail="MCQ count must be between 1 and 20"
        )

    try:
        result = generate_questions(
            topic=topic,
            mcq_count=mcq_count
        )

        return result

    except Exception as e:
        print("AI ERROR:", repr(e))

        raise HTTPException(
            status_code=503,
            detail="AI question generation failed. Please try again later."
        )


# 8. Approve and Save AI Questions
@router.post("/tests/{test_id}/ai/approve", status_code=201)
def approve_ai_questions(
    test_id: int,
    data: AIQuestionsApprove,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    test = db.query(Test).filter(
        Test.id == test_id,
        Test.teacher_id == current_user.id
    ).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    try:
        saved_questions = []

        for item in data.questions:

            new_question = Question(
                test_id=test_id,
                title=item.title,
                description=item.explanation,
                question_type="mcq",
                difficulty=item.difficulty
            )

            db.add(new_question)
            db.flush()

            for index, option_text in enumerate(
                item.options, start=1
            ):
                new_option = QuestionOption(
                    question_id=new_question.id,
                    option_text=option_text,
                    is_correct=(
                        index == item.correct_option
                    )
                )

                db.add(new_option)

            saved_questions.append(new_question.id)

        db.commit()

        return {
            "message": "AI questions approved and saved successfully",
            "test_id": test_id,
            "total_questions": len(saved_questions),
            "question_ids": saved_questions
        }

    except Exception as e:
        db.rollback()
        print("APPROVE ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to save AI questions"
        )


    
@router.get("/tests/{test_id}/questions")
def get_test_questions(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    # Check whether test belongs to this teacher
    test = db.query(Test).filter(
        Test.id == test_id,
        Test.teacher_id == current_user.id
    ).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    # Get all questions of this test
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
                    "option_text": option.option_text,
                    "is_correct": option.is_correct
                }
                for option in options
            ]
        })

    return {
        "test_id": test_id,
        "test_title": test.title,
        "total_questions": len(result),
        "questions": result
    }





@router.post("/tests/{test_id}/coding-questions")
def create_coding_question(
    test_id: int,
    data: CodingQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    test = db.query(Test).filter(
        Test.id == test_id,
        Test.teacher_id == current_user.id
    ).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    question = Question(
        test_id=test_id,
        title=data.title,
        description=data.description,
        question_type="coding",
        difficulty=data.difficulty,
        marks=data.marks,
        allowed_languages=data.allowed_languages
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return {
        "message": "Coding question created successfully",
        "question_id": question.id,
        "title": question.title,
        "allowed_languages": question.allowed_languages,
        "marks": question.marks
    }



@router.post("/questions/{question_id}/test-cases")
def create_test_case(
    question_id: int,
    data: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    question = db.query(Question).join(Test).filter(
        Question.id == question_id,
        Test.teacher_id == current_user.id,
        Question.question_type == "coding"
    ).first()

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Coding question not found"
        )

    test_case = TestCase(
        question_id=question_id,
        input_data=data.input_data,
        expected_output=data.expected_output,
        is_hidden=data.is_hidden,
        marks=data.marks
    )

    db.add(test_case)
    db.commit()
    db.refresh(test_case)

    return {
        "message": "Test case created successfully",
        "test_case_id": test_case.id,
        "question_id": question_id,
        "is_hidden": test_case.is_hidden,
        "marks": test_case.marks
    }





@router.get("/dashboard")
def teacher_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    # Only teachers can access this dashboard
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=403,
            detail="Only teachers allowed"
        )

    # Get tests created by this teacher
    tests = db.query(Test).filter(
        Test.teacher_id == current_user.id
    ).all()

    test_ids = [test.id for test in tests]

    # Get questions and attempts of these tests
    questions = []
    attempts = []

    if test_ids:
        questions = db.query(Question).filter(
            Question.test_id.in_(test_ids)
        ).all()

        attempts = db.query(TestAttempt).filter(
            TestAttempt.test_id.in_(test_ids)
        ).all()

    # Separate completed and pending attempts
    completed_attempts = [
        a for a in attempts if a.status == "submitted"
    ]

    in_progress_attempts = [
        a for a in attempts if a.status == "in_progress"
    ]

    # Count unique students who attempted teacher's tests
    total_students = len(set(
        a.student_id for a in attempts
    ))

    # Calculate average percentage
    percentages = []

    for attempt in completed_attempts:
        test_questions = [
            q for q in questions if q.test_id == attempt.test_id
        ]

        total_marks = sum(
            q.marks if q.marks is not None else 1
            for q in test_questions
        )

        if total_marks > 0:
            percentage = (
                (attempt.score or 0) / total_marks
            ) * 100

            percentages.append(percentage)

    average_percentage = (
        sum(percentages) / len(percentages)
        if percentages else 0
    )

    # Test-wise performance
    test_performance = []

    for test in tests:
        test_questions = [
            q for q in questions if q.test_id == test.id
        ]

        test_attempts = [
            a for a in attempts if a.test_id == test.id
        ]

        submitted = [
            a for a in test_attempts
            if a.status == "submitted"
        ]

        test_percentages = []

        total_marks = sum(
            q.marks if q.marks is not None else 1
            for q in test_questions
        )

        for attempt in submitted:
            if total_marks > 0:
                test_percentages.append(
                    ((attempt.score or 0) / total_marks) * 100
                )

        test_average = (
            sum(test_percentages) / len(test_percentages)
            if test_percentages else 0
        )

        test_performance.append({
            "test_id": test.id,
            "title": test.title,
            "is_active": test.is_active,
            "total_questions": len(test_questions),
            "total_attempts": len(test_attempts),
            "completed_attempts": len(submitted),
            "average_percentage": round(test_average, 2)
        })

    return {
        "teacher": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email
        },

        "statistics": {
            "total_tests_created": len(tests),
            "active_tests": sum(
                1 for test in tests if test.is_active
            ),
            "total_questions_created": len(questions),
            "total_students": total_students,
            "total_attempts": len(attempts),
            "completed_attempts": len(completed_attempts),
            "in_progress_attempts": len(in_progress_attempts)
        },

        "performance": {
            "average_percentage": round(average_percentage, 2)
        },

        "test_performance": test_performance
    }




# 10. Get Student Performance of a Test

@router.get("/tests/{test_id}/results")
def get_test_results(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    # Check test belongs to this teacher
    test = db.query(Test).filter(
        Test.id == test_id,
        Test.teacher_id == current_user.id
    ).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    # Get all questions
    questions = db.query(Question).filter(
        Question.test_id == test_id
    ).all()

    mcq_questions = [
        q for q in questions if q.question_type != "coding"
    ]

    coding_questions = [
        q for q in questions if q.question_type == "coding"
    ]

    total_marks = sum(
        q.marks if q.marks is not None else 1
        for q in questions
    )

    # Get all attempts
    attempts = db.query(TestAttempt).filter(
        TestAttempt.test_id == test_id
    ).all()

    results = []

    for attempt in attempts:

        student = db.query(User).filter(
            User.id == attempt.student_id
        ).first()

        # Get MCQ answers
        answers = db.query(StudentAnswer).filter(
            StudentAnswer.attempt_id == attempt.id
        ).all()

        correct_answers = sum(
            1 for a in answers if a.is_correct
        )

        wrong_answers = sum(
            1 for a in answers if not a.is_correct
        )

        # Calculate MCQ score
        mcq_score = sum(
            q.marks if q.marks is not None else 1
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

        # Calculate coding score
        coding_score = sum(
    (latest_submissions[q.id].score or 0)
    for q in coding_questions
    if (
        q.id in latest_submissions
        and latest_submissions[q.id].status != "pending"
    )
)
    

        # Current score (MCQ + Coding)
        current_score = mcq_score + coding_score

        # Final score only after test submission
        final_score = (
            attempt.score
            if attempt.status == "submitted"
            else None
        )

        # Calculate percentage
        display_score = (
            final_score
            if final_score is not None
            else current_score
        )

        percentage = (
            round((display_score / total_marks) * 100, 2)
            if total_marks > 0 else 0
        )

        results.append({
            "attempt_id": attempt.id,

            "student": {
                "id": student.id if student else None,
                "name": student.name if student else "Unknown",
                "email": student.email if student else "Unknown"
            },

            "status": attempt.status,

            "performance": {
                "mcq_score": mcq_score,
                "coding_score": coding_score,
                "current_score": current_score,
                "final_score": final_score,
                "total_marks": total_marks,
                "percentage": percentage
            },

            "mcq_details": {
                "total_questions": len(mcq_questions),
                "answered": len(answers),
                "correct": correct_answers,
                "wrong": wrong_answers
            },

            "submitted_at": attempt.submitted_at
        })

    return {
        "test_id": test.id,
        "test_title": test.title,
        "total_questions": len(questions),
        "total_attempts": len(attempts),
        "results": results
    }



# 11. Get Detailed Result of a Student Attempt

@router.get("/attempts/{attempt_id}/details")
def get_attempt_details(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    # 1. Find student attempt
    attempt = db.query(TestAttempt).filter(
        TestAttempt.id == attempt_id
    ).first()

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="Attempt not found"
        )

    # 2. Check whether this test belongs to current teacher
    test = db.query(Test).filter(
        Test.id == attempt.test_id,
        Test.teacher_id == current_user.id
    ).first()

    if not test:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to view this result"
        )

    # 3. Get student details
    student = db.query(User).filter(
        User.id == attempt.student_id
    ).first()

    # 4. Get all questions of this test
    questions = db.query(Question).filter(
        Question.test_id == test.id
    ).all()

    # 5. Get student's MCQ answers
    answers = db.query(StudentAnswer).filter(
        StudentAnswer.attempt_id == attempt.id
    ).all()

    answer_map = {
        answer.question_id: answer
        for answer in answers
    }

    # 6. Get coding submissions
    submissions = db.query(CodeSubmission).filter(
        CodeSubmission.attempt_id == attempt.id
    ).order_by(CodeSubmission.id).all()

    latest_submissions = {}

    for submission in submissions:
        latest_submissions[submission.question_id] = submission

    question_details = []

    # 7. Prepare question-wise result
    for question in questions:

        # MCQ Question
        if question.question_type != "coding":

            options = db.query(QuestionOption).filter(
                QuestionOption.question_id == question.id
            ).all()

            student_answer = answer_map.get(question.id)

            selected_option = None
            if student_answer:
                selected_option = next(
                    (
                        option.option_text
                        for option in options
                        if option.id == student_answer.selected_option_id
                    ),
                    None
                )

            correct_options = [
                option.option_text
                for option in options
                if option.is_correct
            ]

            question_details.append({
                "question_id": question.id,
                "question": question.title,
                "description": question.description,
                "question_type": "MCQ",
                "marks": question.marks,
                "selected_answer": selected_option,
                "correct_answer": correct_options,
                "is_correct": (
                    student_answer.is_correct
                    if student_answer else None
                ),
                "marks_obtained": (
                    question.marks if student_answer and student_answer.is_correct
                    else 0
                )
            })

        # Coding Question
        else:

            submission = latest_submissions.get(question.id)

            question_details.append({
                "question_id": question.id,
                "question": question.title,
                "description": question.description,
                "question_type": "coding",
                "programming_language": (
                    submission.programming_language
                    if submission else None
                ),
                "submitted_code": (
                    submission.source_code
                    if submission else None
                ),
                "submission_status": (
                    submission.status
                    if submission else "not_attempted"
                ),
                "marks": question.marks,
                "marks_obtained": (
                    submission.score
                    if submission else 0
                )
            })

    # 8. Return complete result
    return {
        "attempt_id": attempt.id,
        "test": {
            "test_id": test.id,
            "test_title": test.title
        },
        "student": {
            "student_id": student.id if student else None,
            "name": student.name if student else "Unknown",
            "email": student.email if student else "Unknown"
        },
        "status": attempt.status,
        "final_score": attempt.score,
        "submitted_at": attempt.submitted_at,
        "total_questions": len(questions),
        "question_details": question_details
    }
