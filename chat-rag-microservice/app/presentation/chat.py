from fastapi import APIRouter, HTTPException, Query
from app.jobs.queue_service import queue_service, QueueType
from app.worker.chat_worker import ChatWorker
from app.domain import ChatRequest, ChatAsyncResponse, SystemInfoResponse, ExecutionMode, JobStatus
from app.llm.engine import nemotron_engine
from app.llm.nemotron_service import nemotron_service
from app.jobs.idempotency import idempotency
from app.graph.langgraph_rag_service import langgraph_rag_service
from app.infrastructure.logger import logger


router = APIRouter(prefix="/chat", tags=["chat"])


# ========== Helper Functions ==========

async def _route_to_queue(request: ChatRequest) -> tuple[str, QueueType]:
    """
    Route request to appropriate queue based on mode.
    
    Returns:
        (job_id, target_queue)
    """
    # Ensure queue is connected
    if not queue_service.connection:
        await queue_service.connect()
    
    # Determine target queue
    if request.mode == ExecutionMode.GPU:
        # Force GPU queue
        if not nemotron_engine.cuda_available:
            raise HTTPException(
                status_code=503,
                detail="GPU mode requested but not available. Use mode=auto or mode=api instead."
            )
        target_mode: QueueType = "gpu"
    
    elif request.mode == ExecutionMode.API:
        # Force API queue
        target_mode: QueueType = "api"
    
    else:  # AUTO mode
        # Intelligent routing
        if nemotron_engine.cuda_available:
            target_mode: QueueType = "gpu"
            logger.info("AUTO mode: Routing to GPU queue")
        else:
            target_mode: QueueType = "api"
            logger.info("AUTO mode: Routing to API queue (GPU not available)")
    
    # Publish to queue
    job_id = await queue_service.publish_chat_request(request, target_mode)
    
    return job_id, target_mode


# ========== Endpoints ==========

@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info():
    """
    Get available execution modes and system info.
    """
    return SystemInfoResponse(
        available_modes=nemotron_service.get_available_modes(),
        default_mode=nemotron_engine.default_mode
    )


@router.post("", response_model=ChatAsyncResponse)
@idempotency.idempotent("chat")
async def chat(
    request: ChatRequest,
    mode: ExecutionMode = Query(
        default=ExecutionMode.AUTO,
        description="Execution mode: auto (intelligent routing), gpu (force GPU), api (force NVIDIA API)"
    )
):
    """Send chat request with configurable execution mode.
    
    Unified endpoint for chat requests with three execution modes:
    
    - auto: Intelligent routing (prefers GPU, falls back to API if unavailable)
    - gpu: Force native GPU inference (local model, lower latency, no reasoning tokens)
    - api: Force NVIDIA API (always available, supports reasoning tokens)
    
    Args:
        request (ChatRequest): Chat request with message and generation parameters.
        mode (ExecutionMode, optional): Execution mode via query parameter.
            Defaults to ExecutionMode.AUTO.
    
    Returns:
        ChatAsyncResponse: Response containing job_id, status (PENDING), and idempotency_key.
            Use GET /status/{job_id} to check completion status.
    
    Raises:
        HTTPException: 503 if GPU mode requested but GPU not available.
        HTTPException: 500 for internal errors during request processing.
    
    Examples:
        POST /chat?mode=auto - Intelligent routing (default)
        POST /chat?mode=gpu - Force GPU only
        POST /chat?mode=api - Force API only
    """
    try:
        # Override mode from query parameter
        request.mode = mode

        await langgraph_rag_service.register_user_message(
            session_id=request.session_id,
            user_message=request.message,
            patient_context=request.patient_context,
        )
        request.message = await langgraph_rag_service.build_augmented_prompt(
            session_id=request.session_id,
            query=request.message,
        )
        
        job_id, target_queue = await _route_to_queue(request)

        await langgraph_rag_service.remember_job_context(job_id, request.session_id)
        
        return ChatAsyncResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            idempotency_key=request.idempotency_key
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /chat (mode={mode}): {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/status/{job_id}", response_model=ChatAsyncResponse)
async def get_job_status(job_id: str):
    """
    Get status of any job (GPU or API queue).
    
    Status flow:
    - PENDING: Job in queue
    - PROCESSING: Worker processing
    - COMPLETED: Done (result available)
    - FAILED: Error (error message available)
    """
    try:
        worker = ChatWorker()
        result = await worker.get_job_status(job_id)

        if result.status == JobStatus.COMPLETED and result.result:
            await langgraph_rag_service.sync_assistant_from_job(
                job_id=job_id,
                assistant_message=result.result.response,
            )

        return result
    
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
