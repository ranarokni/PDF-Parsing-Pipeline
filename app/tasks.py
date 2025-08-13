# app/tasks.py
import os
from celery import Celery
import requests
import redis as redis_py

BROKER = os.environ.get("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/uploads")

celery = Celery("pdf_worker", broker=BROKER, backend=BACKEND)

def get_redis_client():
    return redis_py.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

@celery.task(bind=True)
def parse_pdf(self, filepath):
    rds = get_redis_client()
    task_id = self.request.id
    rds.set(f"status:{task_id}", "STARTED")

    try:
        with open(filepath, "rb") as f:
            # Tika server accepts PUT to /tika and returns extracted text
            url = "http://tika:9998/tika"
            resp = requests.put(url, data=f, headers={"Accept": "text/plain"}, timeout=120)
            resp.raise_for_status()
            text = resp.text

        # store result in Redis (avoid storing huge files in Redis in production)
        rds.set(f"result:{task_id}", text)
        rds.set(f"status:{task_id}", "SUCCESS")
        return {"task_id": task_id, "status": "SUCCESS"}

    except Exception as e:
        rds.set(f"status:{task_id}", f"FAIL: {str(e)}")
        # re-raise so Celery records failure too
        raise
