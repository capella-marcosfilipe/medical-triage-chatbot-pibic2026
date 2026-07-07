# Implementation Summary

## Overview

The backend is a thin FastAPI gateway for the triage workflow. It manages patient sessions, mocked smartwatch data, and the HTTP contract with the `chat-rag-microservice`.

## Current Backend Responsibilities

1. Create and keep in-memory patient sessions.
2. Generate mocked physiological data for smartwatch retrieval.
3. Enqueue chat jobs and track `chat_id` / `job_id` mappings.
4. Expose job status and conversation resume endpoints.
5. Forward patient context to the microservice when available.

## Current Architecture

```text
app/
├── api/v1/          # REST endpoints
├── core/            # settings and configuration
├── models/          # Pydantic schemas
└── services/        # session, smartwatch and microservice client
```

## Public API Surface

- `POST /api/v1/iniciar_atendimento`
- `GET /api/v1/get_smartwatch_data/{smartwatch_id}`
- `POST /api/v1/chat`
- `GET /api/v1/chat/status/{job_id}`
- `GET /api/v1/chat/{chat_id}`
- `GET /api/v1/obter_ficha_completa/{session_id}`

## Documentation Layout

- `README.md` - setup and quick usage
- `docs/api.md` - endpoint contract
- `docs/deployment.md` - run and deployment notes
- `docs/implementation.md` - architecture summary

## Key Design Notes

- The smartwatch endpoint is mocked and independent from the patient session.
- The chat endpoint is asynchronous and returns `job_id` plus `chat_id`.
- The job status endpoint returns a structured content block when the LLM has responded.
- The conversation can be resumed from `GET /api/v1/chat/{chat_id}`.
