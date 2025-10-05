-- ============================================
-- Snowflake Setup for EY Data Integration
-- Run this ONCE in Snowflake Web UI
-- ============================================

-- 1. Create a dedicated warehouse for data integration
CREATE WAREHOUSE IF NOT EXISTS EY_COMPUTE_WH
  WITH WAREHOUSE_SIZE = 'SMALL'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warehouse for EY Data Integration SaaS';

-- 2. Create database for data integration
CREATE DATABASE IF NOT EXISTS EY_DATA_INTEGRATION
  COMMENT = 'Database for EY Data Integration platform';

-- 3. Use the database
USE DATABASE EY_DATA_INTEGRATION;

-- 4. Create schema (PUBLIC is default, but being explicit)
CREATE SCHEMA IF NOT EXISTS PUBLIC;

-- 5. Grant permissions (adjust role name if needed)
-- If using ACCOUNTADMIN role, you already have permissions
-- If using a custom role, grant permissions:

-- GRANT USAGE ON WAREHOUSE EY_COMPUTE_WH TO ROLE YOUR_ROLE_NAME;
-- GRANT ALL ON DATABASE EY_DATA_INTEGRATION TO ROLE YOUR_ROLE_NAME;
-- GRANT ALL ON SCHEMA EY_DATA_INTEGRATION.PUBLIC TO ROLE YOUR_ROLE_NAME;

-- 6. Verify setup
SHOW WAREHOUSES LIKE 'EY_COMPUTE_WH';
SHOW DATABASES LIKE 'EY_DATA_INTEGRATION';

-- ============================================
-- Done! Now configure your .env file
-- ============================================

/*
Your .env should have:

SNOWFLAKE_ACCOUNT=<from step 1>
SNOWFLAKE_USER=<your username>
SNOWFLAKE_PASSWORD=<your password>
SNOWFLAKE_WAREHOUSE=EY_COMPUTE_WH
SNOWFLAKE_DATABASE=EY_DATA_INTEGRATION
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=ACCOUNTADMIN (or your role)
*/

