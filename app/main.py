from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from enum import Enum
import os

app = FastAPI()


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Task(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    priority: Priority = Priority.medium
    done: bool = False


class TaskOut(Task):
    id: int

# In-memory store for now — swapped for a real DB later
tasks: dict[int, Task] = {}

next_id = 1


@app.get("/")
def read_root():
    return {"Hello": f"From: {os.environ.get('HOSTNAME', 'DEFAULT_ENV')}"}


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(task: Task):
    global next_id
    task_id = next_id
    tasks[task_id] = task
    next_id += 1
    return TaskOut(id=task_id, **task.model_dump())


@app.get("/tasks", response_model=list[TaskOut])
def list_tasks(done: bool | None = None):
    results = [
        TaskOut(id=tid, **t.model_dump())
        for tid, t in tasks.items()
        if done is None or t.done == done
    ]
    return results


@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int):
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut(id=task_id, **task.model_dump())


@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task: Task):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    tasks[task_id] = task
    return TaskOut(id=task_id, **task.model_dump())


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    