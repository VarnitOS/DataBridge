"""
Job state management and file storage
"""
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_APPROVAL = "awaiting_approval"


class JobStore:
    """In-memory job state storage (use Redis/PostgreSQL in production)"""
    
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, dataset1_info: Dict, dataset2_info: Dict) -> str:
        """Create a new session for uploaded datasets"""
        session_id = str(uuid.uuid4())[:8]
        
        self._sessions[session_id] = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "dataset1": dataset1_info,
            "dataset2": dataset2_info,
            "status": "uploaded",
            "snowflake_tables": {
                "dataset1": f"RAW_{session_id}_DATASET_1",
                "dataset2": f"RAW_{session_id}_DATASET_2"
            }
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        return self._sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Update session with new information"""
        if session_id in self._sessions:
            self._sessions[session_id].update(updates)
    
    def create_job(self, session_id: str, job_type: str, metadata: Dict = None) -> str:
        """Create a new job"""
        job_id = f"{job_type}_{session_id}_{str(uuid.uuid4())[:8]}"
        
        self._jobs[job_id] = {
            "job_id": job_id,
            "session_id": session_id,
            "job_type": job_type,
            "status": JobStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "progress_percentage": 0,
            "current_step": None,
            "agents_active": 0,
            "logs": [],
            "errors": [],
            "metadata": metadata or {}
        }
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job information"""
        return self._jobs.get(job_id)
    
    def update_job(self, job_id: str, updates: Dict[str, Any]):
        """Update job with new information"""
        if job_id in self._jobs:
            self._jobs[job_id].update(updates)
    
    def update_job_status(self, job_id: str, status: JobStatus, message: str = None):
        """Update job status"""
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = status.value
            
            if status == JobStatus.IN_PROGRESS and not self._jobs[job_id]["started_at"]:
                self._jobs[job_id]["started_at"] = datetime.utcnow().isoformat()
            
            if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                self._jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
            
            if message:
                self.add_job_log(job_id, message)
    
    def add_job_log(self, job_id: str, message: str):
        """Add log entry to job"""
        if job_id in self._jobs:
            self._jobs[job_id]["logs"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": message
            })
    
    def add_job_error(self, job_id: str, error: str):
        """Add error to job"""
        if job_id in self._jobs:
            self._jobs[job_id]["errors"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": error
            })


# Global job store instance
job_store = JobStore()

