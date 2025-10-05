"""
Snowflake connection pool and management
"""
import snowflake.connector
from snowflake.connector import DictCursor
from typing import Optional, Dict, Any, List
import logging
from contextlib import contextmanager
from core.config import settings
import ssl
import os
import warnings

# Disable SSL verification for hackathon/trial accounts with cert mismatches
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''

# Disable SSL warnings from Snowflake's vendored urllib3
try:
    from snowflake.connector.vendored import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Patch Snowflake's SnowflakeRestful class to disable SSL verification
    import snowflake.connector.network
    from snowflake.connector.vendored.requests.adapters import HTTPAdapter
    from snowflake.connector.vendored.urllib3.util.retry import Retry
    
    # Store the original method
    original_init = snowflake.connector.network.SnowflakeRestful.__init__
    
    def patched_init(self, *args, **kwargs):
        # Call original init
        result = original_init(self, *args, **kwargs)
        
        # Disable SSL verification on the session
        if hasattr(self, '_session') and self._session is not None:
            self._session.verify = False
            logger.info("🔓 Disabled SSL verification on Snowflake HTTP session")
        
        return result
    
    # Apply the patch
    snowflake.connector.network.SnowflakeRestful.__init__ = patched_init
    
except Exception as e:
    logging.getLogger(__name__).warning(f"Could not patch Snowflake SSL: {e}")

logger = logging.getLogger(__name__)


class SnowflakeConnector:
    """Manages Snowflake connections and query execution"""

    def __init__(self):
        self._connection: Optional[snowflake.connector.SnowflakeConnection] = None
        
        # Create custom SSL context that bypasses all verification
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        self._config = {
            "account": settings.SNOWFLAKE_ACCOUNT,
            "user": settings.SNOWFLAKE_USER,
            "password": settings.SNOWFLAKE_PASSWORD,
            "warehouse": settings.SNOWFLAKE_WAREHOUSE,
            "database": settings.SNOWFLAKE_DATABASE,
            "schema": settings.SNOWFLAKE_SCHEMA,
            "role": settings.SNOWFLAKE_ROLE,
            "insecure_mode": True,  # Bypass OCSP checks
            "session_parameters": {
                'PYTHON_CONNECTOR_QUERY_RESULT_FORMAT': 'json'
            }
        }
        
        # Monkey-patch the connection to use unverified SSL after creation
        logger.info("🔓 SSL verification disabled for hackathon/demo environment")
    
    def connect(self) -> snowflake.connector.SnowflakeConnection:
        """Establish connection to Snowflake"""
        try:
            if self._connection is None or self._connection.is_closed():
                logger.info("Connecting to Snowflake...")
                self._connection = snowflake.connector.connect(**self._config)
                logger.info("Successfully connected to Snowflake")
            
            return self._connection
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise
    
    def close(self):
        """Close Snowflake connection"""
        if self._connection and not self._connection.is_closed():
            self._connection.close()
            logger.info("Snowflake connection closed")
    
    @contextmanager
    def get_cursor(self):
        """Get a cursor with automatic cleanup"""
        conn = self.connect()
        cursor = conn.cursor(DictCursor)
        try:
            yield cursor
        finally:
            cursor.close()
    
    async def execute_query(self, query: str, params: Dict = None) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        try:
            with self.get_cursor() as cursor:
                logger.info(f"Executing query: {query[:100]}...")
                cursor.execute(query, params or {})
                results = cursor.fetchall()
                logger.info(f"Query returned {len(results)} rows")
                return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def execute_non_query(self, query: str, params: Dict = None) -> int:
        """Execute a non-query statement (INSERT, UPDATE, DELETE, etc.)"""
        try:
            with self.get_cursor() as cursor:
                logger.info(f"Executing non-query: {query[:100]}...")
                cursor.execute(query, params or {})
                rowcount = cursor.rowcount
                logger.info(f"Non-query affected {rowcount} rows")
                return rowcount
        except Exception as e:
            logger.error(f"Non-query execution failed: {e}")
            raise
    
    async def put_file(self, local_path: str, stage_name: str) -> bool:
        """Upload file to Snowflake stage"""
        try:
            put_query = f"PUT file://{local_path} {stage_name} AUTO_COMPRESS=TRUE OVERWRITE=TRUE"
            await self.execute_non_query(put_query)
            logger.info(f"File uploaded to {stage_name}")
            return True
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise
    
    async def create_stage(self, stage_name: str) -> bool:
        """Create a named stage"""
        try:
            create_query = f"CREATE STAGE IF NOT EXISTS {stage_name}"
            await self.execute_non_query(create_query)
            logger.info(f"Stage created: {stage_name}")
            return True
        except Exception as e:
            logger.error(f"Stage creation failed: {e}")
            raise
    
    async def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        try:
            describe_query = f"DESCRIBE TABLE {table_name}"
            return await self.execute_query(describe_query)
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            raise
    
    async def get_row_count(self, table_name: str) -> int:
        """Get row count for a table"""
        try:
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            result = await self.execute_query(count_query)
            return result[0]["COUNT"] if result else 0
        except Exception as e:
            logger.error(f"Failed to get row count: {e}")
            raise


# Global Snowflake connector instance
snowflake_connector = SnowflakeConnector()

