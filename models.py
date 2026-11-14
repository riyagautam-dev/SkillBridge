
from sqlalchemy import Column, Integer, String,JSON
from database import Base
from sqlalchemy import Text, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student")



class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    duration_minutes = Column(Integer, nullable=False, default=30)



class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    question_type = Column(String(20), nullable=False)
    difficulty = Column(String(20), default="medium")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    programming_language = Column(String(20), nullable=True)
    marks = Column(Integer, default=1)
    allowed_languages = Column(JSON, nullable=True)



class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(
        Integer,
        ForeignKey("questions.id"),
        nullable=False
    )

    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)



class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)

    question_id = Column(
        Integer,
        ForeignKey("questions.id"),
        nullable=False
    )

    input_data = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=False)

    is_hidden = Column(Boolean, default=False)
    marks = Column(Integer, default=1)


  
class TestAttempt(Base):
    __tablename__ = "test_attempts"
    __table_args__ = (
        UniqueConstraint("student_id", "test_id", name="unique_student_test"),
    )


    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_heartbeat = Column(
    DateTime(timezone=True),
    nullable=True
)

    submitted_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default="in_progress")

    score = Column(Integer, nullable=True)
    warning_count = Column(Integer, default=0)
    is_locked = Column(Boolean, default=False)
    termination_reason = Column(String(100), nullable=True) 



class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(Integer, primary_key=True, index=True)

    attempt_id = Column(Integer, ForeignKey("test_attempts.id"), nullable=False)

    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)

    selected_option_id = Column(Integer, ForeignKey("question_options.id"), nullable=False)

    is_correct = Column(Boolean, default=False)

class CodeSubmission(Base):
    __tablename__ = "code_submissions"

    id = Column(Integer, primary_key=True, index=True)

    attempt_id = Column(Integer, ForeignKey("test_attempts.id"), nullable=False)

    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)

    programming_language = Column(String(20), nullable=False)

    source_code = Column(Text, nullable=False)

    status = Column(String(30), default="pending")

    score = Column(Integer, default=0)

    submitted_at = Column(DateTime(timezone=True), server_default=func.now())