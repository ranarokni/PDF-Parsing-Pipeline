# PDF Parsing Pipeline with Docker, Tika, Celery, RabbitMQ, and Redis

This project is to gain a hands on exprience with some of the most important tools in software. It is a fully containerized pipeline for extracting text from PDF files asynchronously.  
It uses **FastAPI** for the API, **Celery** for background task processing, **RabbitMQ** as the message broker, **Redis** for storing results, and **Apache Tika** for PDF parsing.

---

## Features
- Upload single or multiple PDF files
- Asynchronous processing (non-blocking API)
- Text extraction via Apache Tika
- Task status and result retrieval
- Scalable worker architecture

---

## Setup & Run

### **Prerequisites**
- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) installed

### **Steps**
1. Clone this repository
2. Go to the pdf-parsing-pipeline directory
3. docker-compose up --build

That's it! You're good to go!

## Project Workflow

First, you should upload your pdf vie either terminal or the [API Docs](http://localhost:8000/docs), API saves file(s) in a shared volume. After that, API sends task to RabbitMQ with file path and RabbitMQ holds the task until a worker is ready. A celery worker then reads the file, sends it to Apache Tika for parsing and saves extracted text + status in Redis at the end. You can check the status of proccessing tasks and see the results by provided commands. The diagram for the workflow is as follow:

            ┌───────────┐         HTTP          ┌────────────┐
            │  Client   │ ───────────────────▶ │  FastAPI   │
            └───────────┘                      │   API      │
                  ▲                             └─────┬──────┘
                  │                                   │
                  │                                   ▼
                  │                            ┌────────────┐
                  │                            │  Uploads   │
                  │                            │   Folder   │
                  │                            └─────┬──────┘
                  │                                   │
                  │                                   ▼
            ┌─────────────┐     Task Queue     ┌─────────────┐
            │ RabbitMQ    │ ─────────────────▶ │  Celery     │
            │   Queue     │                    │  Worker     │
            └─────────────┘                    └─────┬───────┘
                                                      │
                                                      ▼
                                                ┌────────────┐
                                                │   Tika     │
                                                │  Server    │
                                                └─────┬──────┘
                                                      │
                                                      ▼
                                                ┌────────────┐
                                                │   Redis    │
                                                │   Store    │
                                                └────────────┘



## Testing the System End-to-End

Uplaod the file: 
``` bash
curl -F "file=@/path/to/file.pdf" http://localhost:8000/upload
```

You get the response:
``` bash
{"task_id": "123abc"}

```
You can check status by:

``` bash
curl http://localhost:8000/status/123abc
```
Once the status us "SUCCESS", get the result:

``` bash
curl http://localhost:8000/result/123abc
```


## Take Aways

The main goal of this project was for me to learn and get hands-on experience with the different tools and technologies involved in building an asynchronous PDF parsing pipeline. [Here’s](https://github.com/ranarokni/PDF-Parsing-Pipeline/blob/main/takeaways.md) a summary of what I learned.

