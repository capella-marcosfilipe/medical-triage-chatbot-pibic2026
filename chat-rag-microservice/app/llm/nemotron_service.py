from typing import Generator

import torch
from openai.types.chat import (ChatCompletionSystemMessageParam,
                               ChatCompletionUserMessageParam)

from app.llm.engine import EngineMode, nemotron_engine
from app.infrastructure.constants import (
    NEMOTRON_API_MODEL,
    REASONING_DISABLE_TOKEN,
    REASONING_MAX_THINKING_TOKENS,
    REASONING_MIN_THINKING_TOKENS,
    REASONING_TRIGGER_TOKEN,
)
from app.infrastructure.logger import Logger

logger = Logger()


class NemotronService:
    """Service layer for Nemotron engine."""
    def __init__(self):
        self._engine = nemotron_engine
    
    def get_available_modes(self) -> dict[str, bool]:
        """Get available execution modes."""
        return {
            "gpu": self._engine.cuda_available,
            "api": True  # API always available
        }
    
    def _build_messages(
        self,
        user_message: str,
        use_reasoning: bool
    ) -> list[ChatCompletionUserMessageParam | ChatCompletionSystemMessageParam]:
        """Build messages list with explicit reasoning on/off.

        The model defaults to chain-of-thought reasoning ON when neither
        `/think` nor `/no_think` is sent, so the trigger token is always
        included (never omitted) to make the choice explicit. Without this,
        reasoning tokens silently compete with the structured JSON output
        for the same `max_tokens` budget and can crowd it out entirely.
        """
        trigger = REASONING_TRIGGER_TOKEN if use_reasoning else REASONING_DISABLE_TOKEN
        return [
            ChatCompletionSystemMessageParam(role="system", content=trigger),
            ChatCompletionUserMessageParam(role="user", content=user_message),
        ]
    
    def _generate_gpu(
        self,
        user_message: str,
        max_tokens: int = 512,
        temperature: float = 0.6
    ) -> str:
        """Generate response using local GPU.
        
        Args:
            user_message: User's input
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response string
        """
        # --- Guard Clauses ---
        if not self._engine.cuda_available:
            raise RuntimeError("GPU mode not available on this system")
        
        if not hasattr(self._engine, "gpu_tokenizer") or self._engine.gpu_tokenizer is None:
            raise RuntimeError("GPU tokenizer is not initialized.")
        
        if not hasattr(self._engine, "gpu_model") or self._engine.gpu_model is None:
            raise RuntimeError("GPU model is not initialized.")
        
        # Format message
        messages = [{"role": "user", "content": user_message}]
        
        # Apply chat template
        prompt = self._engine.gpu_tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize
        inputs = self._engine.gpu_tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self._engine.gpu_model.device) for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = self._engine.gpu_model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=0.95,
                pad_token_id=self._engine.gpu_tokenizer.eos_token_id
            )
        
        # Decode
        generated_text = self._engine.gpu_tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        return generated_text.strip()
    
    def _generate_api(
        self,
        user_message: str,
        max_tokens: int = 512,
        temperature: float = 0.6,
        use_reasoning: bool = False
    ) -> str:
        """Generate response using NVIDIA API."""
        messages = self._build_messages(user_message, use_reasoning)
        
        extra_body = {}
        if use_reasoning:
            extra_body = {
                "min_thinking_tokens": REASONING_MIN_THINKING_TOKENS,
                "max_thinking_tokens": REASONING_MAX_THINKING_TOKENS
            }
        
        completion = self._engine.api_client.chat.completions.create(
            model=NEMOTRON_API_MODEL,
            messages=messages,
            temperature=temperature,
            top_p=0.95,
            max_tokens=max_tokens,
            stream=False,
            extra_body=extra_body
        )
        
        choice = completion.choices[0]
        message = choice.message
        reasoning = getattr(message, "reasoning_content", None)

        logger.debug(
            f"[API] finish_reason={choice.finish_reason}, "
            f"content_len={len(message.content or '')}, reasoning_len={len(reasoning or '')}"
        )

        # NEVER fall back to reasoning_content as the response: it is raw
        # chain-of-thought (often in English, often mid-sentence if
        # max_tokens was exhausted before the final answer) and must not
        # reach the patient. If content is empty, the caller's structured
        # JSON parsing will fail and degrade to the safe fallback message.
        if not message.content and reasoning:
            logger.warning(
                "[API] Model returned only reasoning_content (empty final content); "
                f"finish_reason={choice.finish_reason}. Discarding reasoning text "
                "instead of leaking it as the response."
            )

        response = message.content
        if not response and getattr(message, "refusal", None):
            response = message.refusal
            logger.warning("[API] Response was refused")

        if not response:
            logger.error(f"[API] Empty response! finish_reason={choice.finish_reason}")

        return response or ""
    
    def generate_response(
        self,
        user_message: str,
        max_tokens: int = 512,
        temperature: float = 0.6,
        mode: EngineMode | None = None,
        use_reasoning: bool = False
    ) -> str:
        """
        Generate response with automatic or explicit mode selection.
        
        Args:
            user_message: User's input
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            mode: Force 'gpu' or 'api', or None for auto-detect
            use_reasoning: Enable reasoning (API only)
        """
        # Auto-detect mode if not specified
        if mode is None:
            mode = self._engine.default_mode
        
        if mode == "gpu":
            return self._generate_gpu(user_message, max_tokens, temperature)
        else:
            return self._generate_api(user_message, max_tokens, temperature, use_reasoning)
    
    def generate_response_stream(
        self,
        user_message: str,
        max_tokens: int = 512,
        temperature: float = 0.6,
        use_reasoning: bool = False
    ) -> Generator[str, None, None]:
        """Generate streaming response (API only)."""
        messages = self._build_messages(user_message, use_reasoning)
        
        extra_body = {}
        if use_reasoning:
            extra_body = {
                "min_thinking_tokens": REASONING_MIN_THINKING_TOKENS,
                "max_thinking_tokens": REASONING_MAX_THINKING_TOKENS
            }
        
        completion = self._engine.api_client.chat.completions.create(
            model=NEMOTRON_API_MODEL,
            messages=messages,
            temperature=temperature,
            top_p=0.95,
            max_tokens=max_tokens,
            stream=True,
            extra_body=extra_body
        )
        
        for chunk in completion:
            reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
            if reasoning:
                yield reasoning
            
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content


nemotron_service = NemotronService()
