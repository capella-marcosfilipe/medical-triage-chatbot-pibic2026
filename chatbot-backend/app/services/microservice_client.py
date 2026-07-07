"""HTTP client used by chatbot-backend to consume chat-rag-microservice."""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class ChatbotMicroserviceClient:
    """Encapsulate outbound requests to chat-rag-microservice."""

    def __init__(self) -> None:
        self.base_url = settings.chatbot_microservice_url.rstrip("/")
        self.timeout = settings.chatbot_microservice_timeout_seconds

    async def enqueue_chat(self, payload: dict[str, Any], mode: str) -> dict[str, Any]:
        url = f"{self.base_url}/v1/chat"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, params={"mode": mode}, json=payload)
        response.raise_for_status()
        return response.json()

    async def get_chat_status(self, job_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/v1/chat/status/{job_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
        response.raise_for_status()
        return response.json()


chatbot_microservice_client = ChatbotMicroserviceClient()
