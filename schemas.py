
from pydantic import BaseModel, EmailStr, Field
from typing import List, Literal

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None,min_length=2, max_length=100)
    email: EmailStr | None=None



class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    model_config = {
        "from_attributes": True#pydentic v2 ka shi tareeka hai
    }


class Config:
    from_attributes = True



class TeacherRegister(UserCreate):
    invitation_code: str


class TestCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    duration_minutes: int = Field(default=30, ge=1, le=300)



class QuestionCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str
    question_type: Literal["mcq", "coding"]
    difficulty: Literal["easy", "medium", "hard"] = "medium"



from pydantic import field_validator

class QuestionOptionCreate(BaseModel):
    options: list[str] = Field(min_length=4, max_length=4)
    correct_option: int = Field(ge=1, le=4)

    @field_validator("options")
    @classmethod
    def check_options(cls, value):
        if any(not option.strip() for option in value):
            raise ValueError("Options cannot be empty")
        return value



class AIQuestionReview(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_option: int = Field(ge=1, le=4)
    explanation: str
    difficulty: Literal["easy", "medium", "hard"] = "medium"


class AIQuestionsApprove(BaseModel):
    questions: list[AIQuestionReview] = Field(
        min_length=1,
        max_length=20
    )


class StudentAnswerSubmit(BaseModel):
    selected_option_id: int



class CodingQuestionCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)

    difficulty: Literal["easy", "medium", "hard"] = "medium"

    allowed_languages: List[
        Literal["python", "java", "c", "cpp"]
    ] = Field(min_length=1)

    marks: int = Field(default=10, ge=1, le=100)




class CodeSubmissionCreate(BaseModel):
    programming_language: Literal["python", "java", "c", "cpp"]
    source_code: str

class TestCaseCreate(BaseModel):
    input_data: str
    expected_output: str
    is_hidden: bool = False
    marks: int = Field(default=1, ge=0)
