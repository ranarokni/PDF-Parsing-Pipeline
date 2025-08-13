# app/main.py
import os
import uuid
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
import aiofiles
import redis as redis_py
from app.tasks import parse_pdf, celery

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
rds = redis_py.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

app = FastAPI(title="PDF Parsing API")

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    unique_name = f"{uuid.uuid4().hex}.pdf"
    save_path = os.path.join(UPLOAD_DIR, unique_name)
    async with aiofiles.open(save_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    task = parse_pdf.delay(save_path)
    rds.set(f"status:{task.id}", "PENDING")
    return {"task_id": task.id}


@app.post("/upload-multiple")
async def upload_multiple(files: List[UploadFile] = File(...)):
    task_ids = []
    for file in files:
        if file.content_type != "application/pdf":
            continue
        unique_name = f"{uuid.uuid4().hex}.pdf"
        save_path = os.path.join(UPLOAD_DIR, unique_name)
        async with aiofiles.open(save_path, "wb") as out_file:
            await out_file.write(await file.read())

        task = parse_pdf.delay(save_path)
        rds.set(f"status:{task.id}", "PENDING")
        task_ids.append(task.id)

    return {"task_ids": task_ids}



@app.get("/status/{task_id}")
def get_status(task_id: str):
    status = rds.get(f"status:{task_id}")
    if status:
        return {"task_id": task_id, "status": status}
    # fallback to Celery's status
    async_result = celery.AsyncResult(task_id)
    return {"task_id": task_id, "status": async_result.status}

@app.get("/result/{task_id}")
def get_result(task_id: str):
    result = rds.get(f"result:{task_id}")
    if result:
        return {"task_id": task_id, "result": result}
    async_result = celery.AsyncResult(task_id)
    if async_result.successful():
        return {"task_id": task_id, "result": async_result.result}
    return {"task_id": task_id, "status": async_result.status}
