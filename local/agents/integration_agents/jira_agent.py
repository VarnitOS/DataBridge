"""
Jira Agent - Creates and manages Jira tickets
"""
from typing import Dict, Any
import logging
from core.config import settings

logger = logging.getLogger(__name__)


class JiraAgent:
    """
    Jira Agent - Handles Jira integration for conflict escalation
    
    Responsibilities:
    - Create stories for conflicts
    - Update ticket status
    - Track approvals
    """
    
    def __init__(self, agent_id: str, config: Dict = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.jira_client = None
        
        if settings.JIRA_ENABLED:
            try:
                from jira import JIRA
                self.jira_client = JIRA(
                    server=settings.JIRA_URL,
                    basic_auth=(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN)
                )
                logger.info(f"Initialized Jira Agent: {agent_id}")
            except Exception as e:
                logger.warning(f"Jira initialization failed: {e}")
        else:
            logger.info(f"Jira disabled, agent {agent_id} in mock mode")
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Jira task"""
        task_type = task.get("type")
        
        if task_type == "create_ticket":
            return await self.create_ticket(
                task["session_id"],
                task.get("conflict", {})
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def create_ticket(
        self,
        session_id: str,
        conflict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Jira ticket for conflict"""
        logger.info(f"[{self.agent_id}] Creating Jira ticket for {session_id}")
        
        if not self.jira_client:
            logger.info("Jira disabled, returning mock ticket")
            return {
                "ticket_id": f"MOCK-{session_id[:8]}",
                "url": "https://mock-jira.example.com",
                "status": "created"
            }
        
        try:
            # Create actual Jira issue
            issue_dict = {
                'project': {'key': settings.JIRA_PROJECT_KEY},
                'summary': f"Data Integration Conflict - {session_id}",
                'description': conflict.get("issue", "Conflict detected"),
                'issuetype': {'name': 'Story'},
                'labels': ['data-integration', 'auto-created']
            }
            
            new_issue = self.jira_client.create_issue(fields=issue_dict)
            
            return {
                "ticket_id": new_issue.key,
                "url": f"{settings.JIRA_URL}/browse/{new_issue.key}",
                "status": "created"
            }
        
        except Exception as e:
            logger.error(f"Jira ticket creation failed: {e}")
            # Return mock on failure
            return {
                "ticket_id": f"ERROR-{session_id[:8]}",
                "error": str(e)
            }

