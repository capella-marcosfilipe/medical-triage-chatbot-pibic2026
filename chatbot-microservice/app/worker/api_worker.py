import asyncio
import os

from app.model import ChatRequest
from app.utils.logger import logger
from app.worker.base_worker import BaseWorker
from app.worker.strategy import ApiResponseStrategy


class APIWorker(BaseWorker):
    """Worker that processes requests using NVIDIA API."""
    
    def __init__(self):
        super().__init__(queue_type="api")
        self.strategy = ApiResponseStrategy()
    
    async def start(self):
        """Start API worker."""
        logger.info("🌐 API Worker using NVIDIA API endpoint")
        await super().start()
    
    async def generate_response(self, request: ChatRequest) -> str:
        """Generate response using NVIDIA API."""
        logger.debug(
            f"[API] Generating response | "
            f"message: {request.message[:50]}... | "
            f"max_tokens: {request.max_tokens} | "
            f"reasoning: {request.use_reasoning}"
        )

        response = await self.strategy.generate(request)
        
        logger.debug(f"[API] Generation complete: {len(response)} chars")
        return response


async def main():
    """Main entry point for API worker."""
    worker = APIWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        await worker.shutdown()


if __name__ == "__main__":
    # Enable debugpy only when running worker directly
    enable_debug = os.getenv("ENABLE_WORKER_DEBUG", "false").lower() == "true"
    
    if enable_debug:
        try:
            import debugpy
            DEBUG_PORT = 49123
            debugpy.listen(("0.0.0.0", DEBUG_PORT))
            print(f"🔍 Debugger is listening on 0.0.0.0:{DEBUG_PORT}")
        except Exception as e:
            print(f"⚠️  Could not start debugger: {e}")
    
    asyncio.run(main())
