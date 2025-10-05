"""
Snowflake stage management for file uploads
"""
from typing import Optional
import logging
from snowflake.connector import SnowflakeConnection

logger = logging.getLogger(__name__)


class StageManager:
    """Manages Snowflake named stages for data loading"""
    
    def __init__(self, connector):
        self.connector = connector
    
    async def create_session_stage(self, session_id: str, dataset_num: int) -> str:
        """
        Create a named stage for a session's dataset
        
        Args:
            session_id: Session identifier
            dataset_num: Dataset number (1 or 2)
        
        Returns:
            Stage name (e.g., @EY_STAGE_abc123_1)
        """
        stage_name = f"EY_STAGE_{session_id}_{dataset_num}"
        
        try:
            create_query = f"CREATE STAGE IF NOT EXISTS {stage_name}"
            await self.connector.execute_non_query(create_query)
            logger.info(f"Created stage: {stage_name}")
            return f"@{stage_name}"
        except Exception as e:
            logger.error(f"Failed to create stage {stage_name}: {e}")
            raise
    
    async def upload_file_to_stage(
        self, 
        local_path: str, 
        stage_name: str
    ) -> bool:
        """
        Upload a file to a Snowflake stage
        
        Args:
            local_path: Local file path
            stage_name: Snowflake stage name (with or without @)
        
        Returns:
            True if successful
        """
        # Ensure stage name starts with @
        if not stage_name.startswith("@"):
            stage_name = f"@{stage_name}"
        
        try:
            await self.connector.put_file(local_path, stage_name)
            logger.info(f"Uploaded {local_path} to {stage_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    async def list_stage_files(self, stage_name: str) -> list:
        """
        List files in a stage
        
        Args:
            stage_name: Snowflake stage name
        
        Returns:
            List of file information
        """
        if not stage_name.startswith("@"):
            stage_name = f"@{stage_name}"
        
        try:
            list_query = f"LIST {stage_name}"
            results = await self.connector.execute_query(list_query)
            return results
        except Exception as e:
            logger.error(f"Failed to list stage files: {e}")
            raise
    
    async def clean_session_stage(self, session_id: str, dataset_num: int):
        """
        Clean up stage after processing
        
        Args:
            session_id: Session identifier
            dataset_num: Dataset number
        """
        stage_name = f"EY_STAGE_{session_id}_{dataset_num}"
        
        try:
            drop_query = f"DROP STAGE IF EXISTS {stage_name}"
            await self.connector.execute_non_query(drop_query)
            logger.info(f"Cleaned up stage: {stage_name}")
        except Exception as e:
            logger.error(f"Failed to clean stage: {e}")
            # Don't raise - cleanup is best-effort

