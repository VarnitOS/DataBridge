"""
Snowflake Ingestion Agent - Uploads CSV to Snowflake with A2A support
"""
from typing import Dict, Any
import logging
from core.base_agent import BaseAgent
from core.agent_registry import AgentCapability, AgentTool
from sf_infrastructure.connector import snowflake_connector
from sf_infrastructure.stage_manager import StageManager

logger = logging.getLogger(__name__)


class SnowflakeIngestionAgent(BaseAgent):
    """
    Snowflake Ingestion Agent - Handles file upload and table creation
    
    Responsibilities:
    - Upload files to Snowflake stage
    - Create tables from CSV schema
    - Load data using COPY INTO
    
    Exposes tools via A2A registry
    """
    
    def __init__(self, agent_id: str, config: Dict = None):
        self.stage_manager = StageManager(snowflake_connector)
        
        # Initialize base agent (auto-registers with registry)
        super().__init__(
            agent_id=agent_id,
            agent_type="snowflake_ingestion",
            capabilities=[AgentCapability.DATA_INGESTION],
            config=config,
            auto_register=True
        )
    
    def _define_tools(self):
        """Define tools this agent exposes to other agents"""
        self._tools = [
            AgentTool(
                name="ingest_csv_to_snowflake",
                description="Upload CSV file to Snowflake, create table with auto-detected schema, and load data",
                capability=AgentCapability.DATA_INGESTION,
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Local path to CSV file"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Session identifier for grouping datasets"
                        },
                        "dataset_num": {
                            "type": "integer",
                            "description": "Dataset number (1, 2, etc.)"
                        }
                    },
                    "required": ["file_path", "session_id", "dataset_num"]
                },
                handler=self._handle_ingest,
                agent_id=self.agent_id
            )
        ]
    
    async def _handle_ingest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for ingest tool (called via A2A)"""
        return await self.ingest_file(
            file_path=params["file_path"],
            session_id=params["session_id"],
            dataset_num=params["dataset_num"]
        )
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ingestion task"""
        task_type = task.get("type")
        
        if task_type == "ingest_file":
            return await self.ingest_file(
                file_path=task["file_path"],
                session_id=task["session_id"],
                dataset_num=task["dataset_num"]
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def ingest_file(
        self,
        file_path: str,
        session_id: str,
        dataset_num: int
    ) -> Dict[str, Any]:
        """
        Ingest a file into Snowflake using native Snowflake schema inference
        """
        logger.info(f"[{self.agent_id}] Ingesting {file_path}")

        try:
            table_name = f"RAW_{session_id}_DATASET_{dataset_num}"

            # Create stage
            stage_name = await self.stage_manager.create_session_stage(
                session_id,
                dataset_num
            )

            # Upload file to Snowflake stage
            await self.stage_manager.upload_file_to_stage(file_path, stage_name)

            # Create table with proper column names from CSV headers
            await self._create_table_from_csv_headers(file_path, table_name)

            # Load data using COPY INTO (skipping header row)
            await self._copy_into_table(table_name, stage_name)

            # Get row count and column count from Snowflake
            row_count = await snowflake_connector.get_row_count(table_name)
            schema_info = await snowflake_connector.get_table_info(table_name)

            logger.info(f"[{self.agent_id}] Ingestion complete: {table_name}")

            return {
                "table_name": table_name,
                "row_count": row_count,
                "column_count": len(schema_info),
                "stage_name": stage_name
            }

        except Exception as e:
            logger.error(f"[{self.agent_id}] Ingestion failed: {e}")
            raise

    async def _create_table_from_csv_headers(self, file_path: str, table_name: str):
        """
        Create table by reading CSV headers with pandas (reliable method)
        """
        import pandas as pd
        
        try:
            # Read just the headers
            df = pd.read_csv(file_path, nrows=0)
            columns = df.columns.tolist()
            
            logger.info(f"[{self.agent_id}] Detected {len(columns)} columns from CSV headers")
            
            # Create table with all VARCHAR columns (Gemini can suggest better types later)
            col_definitions = ", ".join([f'"{col}" VARCHAR' for col in columns])
            create_sql = f"""
            CREATE OR REPLACE TABLE {table_name} (
                {col_definitions}
            )
            """
            
            await snowflake_connector.execute_non_query(create_sql)
            logger.info(f"[{self.agent_id}] Table {table_name} created with {len(columns)} columns")
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to create table from CSV headers: {e}")
            raise
    
    async def _create_table_with_infer_schema(self, table_name: str, stage_name: str):
        """
        Create Snowflake table using INFER_SCHEMA function
        Snowflake automatically detects column types from CSV
        """
        infer_sql = f"""
        CREATE OR REPLACE TABLE {table_name}
        USING TEMPLATE (
            SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
            FROM TABLE(
                INFER_SCHEMA(
                    LOCATION => '{stage_name}',
                    FILE_FORMAT => 'CSV_FORMAT'
                )
            )
        )
        """
        
        try:
            # First, create the CSV format if it doesn't exist
            format_sql = """
            CREATE FILE FORMAT IF NOT EXISTS CSV_FORMAT
            TYPE = 'CSV'
            PARSE_HEADER = TRUE
            FIELD_OPTIONALLY_ENCLOSED_BY = '"'
            NULL_IF = ('NULL', 'null', '')
            """
            await snowflake_connector.execute_non_query(format_sql)
            
            # Create table with inferred schema
            await snowflake_connector.execute_non_query(infer_sql)
            
        except Exception as e:
            # Fallback: Create table with all VARCHAR columns if INFER_SCHEMA fails
            logger.warning(f"INFER_SCHEMA failed, using fallback method: {e}")
            await self._create_table_fallback(table_name, stage_name)
    
    async def _create_table_fallback(self, table_name: str, stage_name: str):
        """
        Fallback method: Create table with inferred columns from stage
        """
        # Use CREATE TABLE AS SELECT with LIMIT 0 to get structure only
        create_sql = f"""
        CREATE OR REPLACE TABLE {table_name}
        AS
        SELECT *
        FROM {stage_name}
        (FILE_FORMAT => (TYPE = 'CSV' SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '"' INFER_SCHEMA = TRUE))
        LIMIT 0
        """
        await snowflake_connector.execute_non_query(create_sql)
    
    async def _copy_into_table(self, table_name: str, stage_name: str):
        """Load data from stage into table (skipping CSV header row)"""
        copy_sql = f"""
        COPY INTO {table_name}
        FROM {stage_name}
        FILE_FORMAT = (
            TYPE = 'CSV' 
            SKIP_HEADER = 1
            FIELD_OPTIONALLY_ENCLOSED_BY = '"'
            NULL_IF = ('NULL', 'null', '')
        )
        ON_ERROR = 'CONTINUE'
        """
        
        await snowflake_connector.execute_non_query(copy_sql)