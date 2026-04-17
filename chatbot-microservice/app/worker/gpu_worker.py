import asyncio

from app.engine.nemotron import nemotron_engine
from app.model import ChatRequest
from app.utils.logger import logger
from app.worker.base_worker import BaseWorker
from app.worker.strategy import GpuResponseStrategy


class GPUWorker(BaseWorker):
    """Worker that processes requests using local GPU."""
    
    def __init__(self):
        super().__init__(queue_type="gpu")
        self.engine = nemotron_engine
        self.strategy = GpuResponseStrategy()
    
    async def start(self):
        """Start GPU worker with GPU validation."""
        # Verify GPU is available
        if not self.engine.cuda_available:
            logger.error("❌ GPU Worker cannot start: CUDA not available")
            raise RuntimeError(
                "GPU not available for GPU worker. "
                "Either run on a machine with GPU or use API worker only."
            )
        
        logger.info(f"🎮 GPU detected: {getattr(self.engine, 'device', 'unknown device')}")
        logger.info(f"Model loaded: {self.engine.gpu_model is not None}")
        
        await super().start()
    
    async def generate_response(self, request: ChatRequest) -> str:
        """Generate response using local GPU."""
        logger.debug(
            f"[GPU] Generating response | "
            f"message: {request.message[:50]}... | "
            f"max_tokens: {request.max_tokens} | "
            f"device: {getattr(self.engine, 'device', 'unknown')}"
        )

        response = await self.strategy.generate(request)
        
        logger.debug(f"[GPU] Generation complete: {len(response)} chars")
        return response


async def main():
    """Main entry point for GPU worker."""
    worker = GPUWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        await worker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
