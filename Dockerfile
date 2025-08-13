FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# create uploads dir (mounted by docker-compose)
RUN mkdir -p /app/uploads

ENV PYTHONUNBUFFERED=1