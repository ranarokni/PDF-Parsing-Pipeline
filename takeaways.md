## What I learned

The main goal of this project was for me to learn and get hands-on experience with the different tools and technologies involved in building an asynchronous PDF parsing pipeline. Here’s a summary of what I learned:

## Docker
Docker is a platform that lets you package applications into standardized units called containers. A container includes everything the application needs to run — code, libraries, dependencies, system tools, and even specific runtime versions.
You can think of Docker as a lightweight operating system for containers: instead of installing software directly on your computer and worrying about version conflicts, Docker creates isolated environments so multiple applications can run with different versions of the same software without interfering with each other.
It works by taking a "snapshot" of the required files, dependencies, and configurations, bundling them together into an image, and then running that image as a container on any machine with Docker installed — making the app portable and consistent. Here is a short description of some important docker architecture concepts in this project:
**Docker Image**: A Docker image is like a blueprint for running your application — it contains your code, its dependencies, and the environment it needs to run. You don’t run an image directly; you use it to create containers.
In this project, the Docker image for the api and worker containers includes:
- Python

- FastAPI and Celery code

- All required Python packages

- Configurations (like upload directory structure)

**Docker Container**: A container is a running instance of a Docker image.
Think of an image as the recipe, and the container as the cake baked from it.
When you run docker run or docker-compose up, you’re creating containers from images.

In this project:

- API container: runs the FastAPI server.

- Worker container: runs the Celery worker process.

- RabbitMQ container: runs the message broker.

- Redis container: runs the in-memory database.

- Tika container: runs the document parsing service.

**Dockerfile**: The Dockerfile defines how to build your image.
It’s a step-by-step set of instructions:

- Which base image to use (python:3.11-slim in our case)

- Copy project files into the image

- Install dependencies (pip install -r requirements.txt)

- Set environment variables

- Specify working directories and default folders

The Dockerfile is what lets anyone recreate the environment exactly, anywhere.


**docker build**: docker build reads the Dockerfile and creates an image.
In docker-compose up --build, the --build flag ensures all images are rebuilt from the latest code and dependencies.

```bash
docker build -t pdf-pipeline-api .
```
This tags the image as pdf-pipeline-api so you can run it later.


**docker run**: docker run creates and starts a container from an image.
If you wanted to run the API manually (without Docker Compose), you could do:
```bash
docker run -p 8000:8000 pdf-pipeline-api
```
This starts the API container and maps its port 8000 to your host’s 8000.


**docker-compose**: Docker Compose is a tool for defining and running multi-container applications.
Instead of manually starting five different containers with multiple docker run commands, docker-compose.yml lets you:

- Declare all services (API, worker, RabbitMQ, Redis, Tika)

- Set their ports, volumes, environment variables, and dependencies

- Start/stop them all at once with docker-compose up and docker-compose down

In this project, docker-compose makes it trivial to spin up the entire pipeline in one command.

**Volumes**: Volumes are how Docker stores data outside of containers so it’s not lost when the container stops.
We use a named volume uploads so the API and worker can share uploaded files.

**Networks**: Docker Compose automatically creates a network where all your services can talk to each other using their service names (e.g., rabbitmq instead of an IP address).
This is why, in our Celery config, we can write:
```bash
broker_url = "amqp://guest:guest@rabbitmq:5672//"
```
and it works without knowing the container’s IP.

For this project, the lifecycle looks like this:

1. Write code → main.py, tasks.py, Dockerfile, docker-compose.yml

2. Build images → docker-compose up --build compiles images from Dockerfiles

3. Start containers → Compose runs each service container

4. Networking → Compose creates a network where services communicate by name

5. Volumes → Files and data shared between containers via mounted volumes



A great place to start learning Docker is this [YouTube playlist](https://youtube.com/playlist?list=PLlsmxlJgn1HK2hnazfLBl8szdF_5e64GE&si=jra8MWriz658qyiX).


## RabbitMQ
RabbitMQ is a message broker, a system that allows different services to communicate asynchronously. In simpler terms, it sits between producers (services sending tasks or messages) and consumers (services processing them) so they don’t need to know about each other’s location, speed, or availability.
This makes the system more reliable: even if the worker is busy or temporarily offline, messages are safely queued until they can be processed.

## FastAPI
FastAPI is a modern, high-performance web framework for building APIs in Python. It’s designed for speed, easy validation, and automatic documentation. In this project, FastAPI handles file uploads, status checks, and result retrieval, acting as the entry point for clients.

## Celery
Celery is a distributed task queue that handles background jobs. It integrates with a broker (RabbitMQ in this case) to fetch tasks and process them asynchronously. Celery also supports scheduling, retries, and monitoring task states — making it ideal for workloads that take time to complete, like parsing large PDFs


## Tika
Apache Tika is a document text extraction toolkit. It detects file types and extracts text, metadata, and language information from various formats such as PDF, DOCX, HTML, and more. In this project, Tika is the engine that converts uploaded PDFs into plain text.

## Redis
Redis is an in-memory key-value data store, meaning it keeps data in RAM for extremely fast access. It’s often used for caching, storing temporary states, or managing queues.
In this project, Redis stores:

- Task status (e.g., PENDING, STARTED, SUCCESS, FAILED)

- Parsed text results for quick retrieval without re-parsing the PDF.
  
Because it’s in-memory, Redis is blazing fast, but data is temporary unless persistence is configured.

---

The main question I had during this project was: why do we separate the API from Celery workers? And even before that — why do we need Celery and RabbitMQ in the first place? The answer to the second question is that Celery and RabbitMQ make it possible to handle multiple requests efficiently without overloading the server. Without them, the API would try to process each PDF in real time, meaning a single large or slow request could block the entire application and even cause it to crash. By introducing RabbitMQ as a message broker and Celery as a background task processor, we ensure that the API can respond instantly with a task_id while the actual work happens asynchronously in the background, keeping the API always responsive.

As for why we separate the API and the workers into different containers, the reasoning comes down to architecture and scalability. In this project, the API (FastAPI container) acts like a waiter in a restaurant — taking orders (file uploads), returning task IDs, and providing status or results. The worker (Celery worker container) is like the chef in the kitchen — doing the heavy lifting of parsing PDFs via Tika. RabbitMQ serves as the ticket board between them, holding orders until a chef is ready. If the waiter tried to cook the meals too, customers would wait far too long before even placing another order. By splitting these roles, the API can always respond quickly, while the workers handle the computationally heavy tasks in parallel. This separation brings several benefits: responsiveness (a slow PDF won’t freeze the API), scalability (we can add more workers or API instances independently), fault isolation (a worker crash won’t take down the API), and asynchronous processing (tasks wait in RabbitMQ until a worker is available, so no requests are lost). The two components never communicate directly; instead, the API sends tasks to RabbitMQ, workers consume those tasks, store results in Redis, and the API retrieves the results for the client. This clean separation is one of the most important design choices in building scalable and resilient pipelines like this one.