from typing import Optional
from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    title: str = Field(..., description="Title of the task")
    done: bool = Field(default=False, description="Completion status of the task")

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, description="Updated task title")
    done: Optional[bool] = Field(default=None, description="Updated completion status")

class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool
