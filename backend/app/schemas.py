from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    target_role_id: Optional[int] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    target_role_id: Optional[int] = None


class SkillLevelsIn(BaseModel):
    levels: Dict[int, int]


class QuizSubmit(BaseModel):
    # One selected option index per question, in the order the questions were shown.
    answers: List[int]
