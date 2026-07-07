"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as api_v1_router
from app.core.config import settings
import uvicorn

app = FastAPI(
    title="Chatbot Triagem Médica API",
    description="REST API for medical triage chatbot with LLM support",
    version="1.0.0",
)

# Configure CORS for frontend compatibility
# In production, use specific origins from settings
allowed_origins = ["*"] if settings.debug else [settings.frontend_url]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 routes
app.include_router(api_v1_router, prefix="/api/v1", tags=["Medical Triage"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Chatbot Triagem Médica API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
