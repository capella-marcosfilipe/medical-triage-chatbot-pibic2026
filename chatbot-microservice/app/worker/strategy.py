"""Response generation strategies for NLP workers."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.model import ChatRequest
from app.service.nemotron_service import nemotron_service


class ResponseGenerationStrategy:
    """Strategy interface for worker response generation."""

    async def generate(self, request: ChatRequest) -> str:
        raise NotImplementedError


@dataclass
class ApiResponseStrategy(ResponseGenerationStrategy):
    """Strategy that delegates generation to NVIDIA API."""

    async def generate(self, request: ChatRequest) -> str:
        return await asyncio.to_thread(
            nemotron_service.generate_response,
            user_message=request.message,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            mode="api",
            use_reasoning=request.use_reasoning,
        )


@dataclass
class GpuResponseStrategy(ResponseGenerationStrategy):
    """Strategy that delegates generation to local GPU."""

    async def generate(self, request: ChatRequest) -> str:
        return await asyncio.to_thread(
            nemotron_service.generate_response,
            user_message=request.message,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            mode="gpu",
            use_reasoning=request.use_reasoning,
        )
