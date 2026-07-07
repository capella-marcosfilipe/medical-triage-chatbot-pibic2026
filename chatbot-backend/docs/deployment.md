# Deployment Guide

This guide covers the current FastAPI backend and its integration with the `chat-rag-microservice`.

## Prerequisites

- Python 3.10 or higher
- Git
- Docker and Docker Compose for full-stack runs

## Local Development

### Backend only

```bash
cd chatbot-backend
cp .env.example .env
pip install -r requirements.txt
python main.py
```

### Full stack

From the repository root:

```bash
docker compose up --build
```

The backend will call the microservice through `CHATBOT_MICROSERVICE_URL`.

## Environment Variables

### chatbot-backend/.env

- `APP_HOST` - default `0.0.0.0`
- `APP_PORT` - default `8001`
- `DEBUG` - default `False`
- `FRONTEND_URL` - CORS origin
- `CHATBOT_MICROSERVICE_URL` - default `http://chat-rag-microservice:8000`

### chat-rag-microservice/.env

- `NVIDIA_API_KEY` - required by the LLM provider
- `RABBITMQ_HOST`, `REDIS_HOST` - infrastructure dependencies

## Docker Compose

The root `docker-compose.yml` starts:

- `chatbot-backend`
- `chat-rag-microservice`
- API worker
- optional GPU worker
- RabbitMQ
- Redis

## Production Notes

- Run the backend behind a reverse proxy or platform service.
- Keep the microservice and workers on the same network.
- Persist Redis/RabbitMQ volumes if you need job continuity across restarts.
