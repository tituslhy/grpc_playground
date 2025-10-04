from pydantic import BaseModel
from typing import List

class TodoCreate(BaseModel):
    task: str

class TodoUpdate(BaseModel):
    task: str

class TodoResponse(BaseModel):
    id: int
    task: str

class TodoListResponse(BaseModel):
    todos: List[TodoResponse]

class DeleteResponse(BaseModel):
    success: bool
    message: str

class TodoCreateBatch(BaseModel):
    tasks: List[str]

class TodoDeleteBatch(BaseModel):
    ids: List[int]

class BatchResponse(BaseModel):
    success_count: int
    failure_count: int
    results: List[TodoResponse]