"""
FastAPI routes for EY Data Integration SaaS
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
import os
import aiofiles
import asyncio
from datetime import datetime
import logging

from api.models import (
    UploadResponse, AnalyzeRequest, AnalyzeResponse,
    ApproveRequest, ApproveResponse, JobStatusResponse,
    ValidateResponse, ChatRequest, ChatResponse, HealthResponse,
    DatasetInfo
)
from core.config import settings
from core.storage import job_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["EY Data Integration"])

# Create upload/output directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_datasets(
    dataset1: UploadFile = File(...),
    dataset2: UploadFile = File(...)
):
    """
    Upload two datasets for integration
    
    - **dataset1**: First CSV/Excel file
    - **dataset2**: Second CSV/Excel file
    
    Returns session_id for tracking the merge pipeline
    """
    try:
        # Validate file extensions
        def validate_extension(filename: str) -> bool:
            ext = filename.split('.')[-1].lower()
            return ext in settings.allowed_extensions_list
        
        if not validate_extension(dataset1.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file format for dataset1. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )
        
        if not validate_extension(dataset2.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format for dataset2. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Generate session ID
        from core.storage import job_store
        import uuid
        session_id = str(uuid.uuid4())[:8]
        
        # Save files
        file1_path = f"uploads/{session_id}_dataset1_{dataset1.filename}"
        file2_path = f"uploads/{session_id}_dataset2_{dataset2.filename}"
        
        async with aiofiles.open(file1_path, 'wb') as f:
            content = await dataset1.read()
            await f.write(content)
        
        async with aiofiles.open(file2_path, 'wb') as f:
            content = await dataset2.read()
            await f.write(content)
        
        logger.info(f"Files uploaded for session {session_id}")
        
        # Create dataset info
        dataset1_info = DatasetInfo(
            filename=dataset1.filename,
            size_bytes=len(content),
            snowflake_table=f"RAW_{session_id}_DATASET_1"
        )
        
        dataset2_info = DatasetInfo(
            filename=dataset2.filename,
            size_bytes=len(content),
            snowflake_table=f"RAW_{session_id}_DATASET_2"
        )
        
        # Store session
        job_store.create_session(
            dataset1_info=dataset1_info.dict(),
            dataset2_info=dataset2_info.dict()
        )
        
        # Update with file paths
        job_store.update_session(session_id, {
            "file1_path": file1_path,
            "file2_path": file2_path
        })
        
        # TODO: Trigger Snowflake ingestion agents asynchronously
        # This will be implemented in Phase 2
        
        return UploadResponse(
            session_id=session_id,
            status="uploaded",
            dataset1=dataset1_info,
            dataset2=dataset2_info
        )
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_schemas(request: AnalyzeRequest):
    """
    Analyze schemas and propose column mappings using Gemini 2.5 Pro
    
    - **session_id**: Session identifier from upload
    
    Returns proposed mappings and conflicts
    """
    import time
    try:
        session = job_store.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        start_time = time.time()
        
        # Trigger Master Agent → Gemini Agent Pool → Real Agent Orchestration!
        from agents.master_agent import master_agent
        
        logger.info(f"🚀 Triggering Master Agent for session {request.session_id}")
        
        # Phase 1: Master Agent analyzes datasets and allocates resources
        await master_agent.analyze_datasets(request.session_id)
        
        # Phase 2: Initiate Gemini agent pool for schema mapping
        mapping_result = await master_agent.initiate_schema_mapping(request.session_id)
        
        processing_time = time.time() - start_time
        
        logger.info(f"✅ Analysis complete in {processing_time:.2f}s")
        
        return AnalyzeResponse(
            status="ready_to_merge",
            mappings=mapping_result.get("mappings", []),
            conflicts=mapping_result.get("conflicts", []),
            schema_analysis=mapping_result.get("schema_analysis", {}),
            processing_time_seconds=processing_time
        )
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve", response_model=ApproveResponse)
async def approve_mappings(request: ApproveRequest):
    """
    Approve column mappings and start merge operation
    
    - **session_id**: Session identifier
    - **approved_mappings**: User-approved column mappings
    - **merge_type**: Type of join (full_outer, inner, left, right)
    - **conflict_resolutions**: Resolutions for conflicts (if any)
    
    Returns job_id for tracking merge progress
    """
    try:
        session = job_store.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Create merge job
        job_id = job_store.create_job(
            session_id=request.session_id,
            job_type="merge",
            metadata={
                "mappings": [m.dict() for m in request.approved_mappings],
                "merge_type": request.merge_type.value
            }
        )
        
        # Trigger Master Agent → Merge Agent Pool → Real Merge Pipeline!
        from agents.master_agent import master_agent
        
        logger.info(f"🚀 Triggering Merge Pipeline for job {job_id}")
        
        # Execute merge asynchronously (fire and forget)
        asyncio.create_task(
            master_agent.execute_merge(
                job_id=job_id,
                session_id=request.session_id,
                approved_mappings=[m.dict() for m in request.approved_mappings],
                merge_type=request.merge_type.value
            )
        )
        
        # Get allocation info
        allocation = master_agent.agent_allocations.get(request.session_id, {
            "merge_agents": 5,
            "quality_agents": 5
        })
        
        return ApproveResponse(
            job_id=job_id,
            status="in_progress",
            estimated_duration_seconds=60.0,
            agents_spawned={
                "merge_agents": allocation.get("merge_agents", 5),
                "quality_agents": allocation.get("quality_agents", 5)
            },
            snowflake_warehouse="LARGE"
        )
    
    except Exception as e:
        logger.error(f"Approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get status of a merge job
    
    - **job_id**: Job identifier from approve endpoint
    
    Returns current job status and progress
    """
    try:
        job = job_store.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Calculate elapsed time if started
        elapsed = None
        if job.get("started_at"):
            start = datetime.fromisoformat(job["started_at"])
            elapsed = (datetime.utcnow() - start).total_seconds()
        
        return JobStatusResponse(
            job_id=job["job_id"],
            status=job["status"],
            progress_percentage=job["progress_percentage"],
            current_step=job.get("current_step"),
            agents_active=job["agents_active"],
            elapsed_time_seconds=elapsed,
            logs=job["logs"],
            errors=job["errors"]
        )
    
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ValidateResponse)
async def validate_merge(session_id: str):
    """
    Run quality validation on merged dataset
    
    - **session_id**: Session identifier
    
    Returns quality report with checks and recommendations
    """
    try:
        session = job_store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # TODO: Trigger Quality Agent Pool
        # This will be implemented in Phase 4
        
        return ValidateResponse(
            overall_status="passed",
            checks={},
            recommendations=[],
            jira_tickets=[]
        )
    
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{session_id}")
async def download_merged_dataset(session_id: str, format: str = "csv"):
    """
    Download merged dataset and mapping report
    
    - **session_id**: Session identifier
    - **format**: Output format (csv, xlsx, parquet)
    
    Returns file download
    """
    try:
        session = job_store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # TODO: Export from Snowflake and return file
        # This will be implemented in Phase 3
        
        output_path = f"outputs/merged_{session_id}.{format}"
        
        if not os.path.exists(output_path):
            raise HTTPException(status_code=404, detail="Merged dataset not ready")
        
        return FileResponse(
            output_path,
            media_type="application/octet-stream",
            filename=f"merged_{session_id}.{format}"
        )
    
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{session_id}")
async def get_mapping_report(session_id: str):
    """
    Get detailed mapping report for a session
    
    - **session_id**: Session identifier
    
    Returns comprehensive report with mappings, quality metrics, etc.
    """
    try:
        session = job_store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # TODO: Generate comprehensive report
        # This will be implemented in Phase 6
        
        return {
            "session_id": session_id,
            "generated_at": datetime.utcnow().isoformat(),
            "datasets": session,
            "mappings": [],
            "quality_report": {},
            "jira_tickets": []
        }
    
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat_with_master_agent(request: ChatRequest):
    """
    Chat with Master Agent for natural language queries
    
    - **query**: Natural language question
    - **session_id**: Optional session context
    - **context**: Optional additional context
    
    Returns AI-generated response with reasoning
    """
    try:
        # Import conversational agent
        from agents.orchestration.conversational_agent import ConversationalAgent
        
        # Get or create conversational agent for this session
        session_id = request.session_id or "default_session"
        agent = ConversationalAgent(agent_id=f"assistant_{session_id}")
        
        # Chat with the agent
        response = await agent.chat(
            user_message=request.message,
            context={"session_id": session_id}
        )
        
        # Determine confidence based on success and actions
        confidence = 95 if response.get("success") else 50
        
        # Build reasoning
        reasoning = None
        if response.get("actions_taken"):
            action_names = [a.get("description", "") for a in response["actions_taken"]]
            reasoning = f"Executed {len(action_names)} agent actions: {', '.join(action_names)}"
        
        return ChatResponse(
            answer=response.get("message", "I'm not sure how to help with that."),
            confidence=confidence,
            reasoning=reasoning,
            suggested_action={"next_steps": response.get("actions_taken", [])} if response.get("actions_taken") else None
        )
    
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        return ChatResponse(
            answer=f"I encountered an error: {str(e)}. Please try again or check the system status.",
            confidence=0,
            reasoning=f"Error: {type(e).__name__}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns system health status and available services
    """
    try:
        # TODO: Check actual service connections
        # For now, return mock healthy status
        
        return HealthResponse(
            status="healthy",
            services={
                "snowflake": "connected",
                "gemini": "available",
                "jira": "connected" if settings.JIRA_ENABLED else "disabled",
                "datadog": "enabled" if settings.DATADOG_ENABLED else "disabled"
            },
            agents={
                "master_agent": "running",
                "agent_pools": {
                    "gemini": 0,
                    "merge": 0,
                    "quality": 0
                }
            }
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

