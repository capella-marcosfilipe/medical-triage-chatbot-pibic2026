"""FastAPI entrypoint for chatbot microservice."""
from fastapi import FastAPI
import uvicorn

from app.config.settings import settings
from app.controller.chat_controller import router as chat_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Chatbot microservice with LangGraph memory, RAG and async LLM workers",
    version="1.0.0",
)

app.include_router(chat_router, prefix="/v1")


@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
