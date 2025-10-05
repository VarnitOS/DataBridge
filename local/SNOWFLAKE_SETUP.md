# ❄️ Snowflake Setup Guide

## Quick Setup (5 Minutes)

### Step 1: Login to Snowflake

Go to your Snowflake web interface:
```
https://[your-account].snowflakecomputing.com
```

### Step 2: Run Setup SQL

1. Click **Worksheets** in the left sidebar
2. Copy and paste the contents of `snowflake_setup.sql`
3. Click **Run All** (or press Ctrl+Enter)

This creates:
- ✅ Warehouse: `EY_COMPUTE_WH` (auto-suspend to save costs)
- ✅ Database: `EY_DATA_INTEGRATION`
- ✅ Schema: `PUBLIC`

### Step 3: Get Your Account Identifier

**Option A: From URL**
Your Snowflake URL looks like:
```
https://ABC12345.us-east-1.snowflakecomputing.com
         ^^^^^^^^^^^^^^^^
         This is your ACCOUNT
```

**Option B: Run SQL**
```sql
SELECT CURRENT_ACCOUNT() || '.' || CURRENT_REGION() as ACCOUNT_IDENTIFIER;
```

**Option C: From UI**
- Click your name (top right)
- Click on the account name
- Copy the **Account Identifier**

### Step 4: Fill in Your `.env` File

Open the `.env` file and replace these values:

```bash
# 1. Your account identifier
SNOWFLAKE_ACCOUNT=ABC12345.us-east-1
#                 ^^^^^^^^^^^^^^^^^^^
#                 Replace this!

# 2. Your username (login email or username)
SNOWFLAKE_USER=your_email@company.com
#              ^^^^^^^^^^^^^^^^^^^^^^^^
#              Your Snowflake login

# 3. Your password
SNOWFLAKE_PASSWORD=YourPassword123
#                  ^^^^^^^^^^^^^^^
#                  Your Snowflake password

# 4. Warehouse (from SQL setup)
SNOWFLAKE_WAREHOUSE=EY_COMPUTE_WH
#                   ^^^^^^^^^^^^^
#                   Already correct!

# 5. Database (from SQL setup)
SNOWFLAKE_DATABASE=EY_DATA_INTEGRATION
#                  ^^^^^^^^^^^^^^^^^^^^
#                  Already correct!

# 6. Your role (check in Snowflake UI)
SNOWFLAKE_ROLE=ACCOUNTADMIN
#              ^^^^^^^^^^^^
#              Usually ACCOUNTADMIN or SYSADMIN
```

### Step 5: Test Connection

```bash
# Start the server
python main.py

# You should see:
# 🔵 Using REAL Snowflake connector
# ✅ Successfully connected to Snowflake
```

If connection fails, see **Troubleshooting** below.

---

## Common Account Identifier Formats

```bash
# AWS (most common)
ABC12345.us-east-1
ABC12345.us-west-2.aws
ABC12345.eu-west-1.aws

# Azure
ABC12345.east-us-2.azure
ABC12345.west-europe.azure

# GCP
ABC12345.us-central1.gcp
ABC12345.europe-west4.gcp

# Organization format (new accounts)
myorg-myaccount
your-company-prod
```

---

## Roles Explained

| Role | Access Level | Recommended For |
|------|-------------|-----------------|
| `ACCOUNTADMIN` | Full access | Hackathon/dev (easiest) |
| `SYSADMIN` | Admin tasks | Production |
| `SECURITYADMIN` | Security only | Limited use |
| Custom Role | Varies | Enterprise setups |

**For hackathon**: Use `ACCOUNTADMIN` (simplest)

---

## Warehouse Sizes & Costs

The setup creates a **SMALL** warehouse:

| Size | Credits/Hour | Use Case | Monthly Cost* |
|------|--------------|----------|---------------|
| X-SMALL | 1 | Testing | ~$72 |
| **SMALL** | 2 | **Dev/Hackathon** | **~$144** |
| MEDIUM | 4 | Production small | ~$288 |
| LARGE | 8 | Production med | ~$576 |
| X-LARGE | 16 | Production large | ~$1,152 |

*Based on $3/credit, assumes continuous use. Auto-suspend saves costs!

**Our setup auto-suspends after 5 minutes** of inactivity, so costs are minimal.

---

## Verify Setup

Run these in Snowflake to verify:

```sql
-- 1. Check warehouse exists
SHOW WAREHOUSES LIKE 'EY_COMPUTE_WH';

-- 2. Check database exists
SHOW DATABASES LIKE 'EY_DATA_INTEGRATION';

-- 3. Test warehouse
USE WAREHOUSE EY_COMPUTE_WH;

-- 4. Test database
USE DATABASE EY_DATA_INTEGRATION;
USE SCHEMA PUBLIC;

-- 5. Test table creation (cleanup test)
CREATE OR REPLACE TABLE TEST_TABLE (id INT, name VARCHAR);
INSERT INTO TEST_TABLE VALUES (1, 'Test');
SELECT * FROM TEST_TABLE;
DROP TABLE TEST_TABLE;
```

If all commands work, you're ready! ✅

---

## Troubleshooting

### Error: "Invalid account name"
**Problem**: Wrong `SNOWFLAKE_ACCOUNT` format

**Solutions**:
1. Try without region: `ABC12345` (just the account)
2. Try with cloud: `ABC12345.us-east-1.aws`
3. Check Snowflake URL for exact format

### Error: "Authentication failed"
**Problem**: Wrong username or password

**Solutions**:
1. Verify username (might be email, might be username)
2. Check password (try logging into Snowflake web UI)
3. Check if SSO is enabled (if so, need to create database user)

### Error: "Warehouse not found"
**Problem**: Warehouse doesn't exist or no permissions

**Solutions**:
1. Run `snowflake_setup.sql` again
2. Grant permissions:
   ```sql
   GRANT USAGE ON WAREHOUSE EY_COMPUTE_WH TO ROLE ACCOUNTADMIN;
   ```

### Error: "Database not found"
**Problem**: Database doesn't exist or no permissions

**Solutions**:
1. Run `snowflake_setup.sql` again
2. Grant permissions:
   ```sql
   GRANT ALL ON DATABASE EY_DATA_INTEGRATION TO ROLE ACCOUNTADMIN;
   ```

### Error: "Connection timeout"
**Problem**: Network/firewall issue

**Solutions**:
1. Check if you're on VPN (might block Snowflake)
2. Check corporate firewall settings
3. Try different network

---

## Example `.env` (Filled Out)

```bash
SNOWFLAKE_ENABLED=true
SNOWFLAKE_ACCOUNT=abc12345.us-east-1
SNOWFLAKE_USER=john.doe@eycompany.com
SNOWFLAKE_PASSWORD=MySecurePass123!
SNOWFLAKE_WAREHOUSE=EY_COMPUTE_WH
SNOWFLAKE_DATABASE=EY_DATA_INTEGRATION
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=ACCOUNTADMIN

GEMINI_API_KEY=AIzaSy...your_actual_key
GEMINI_MODEL=gemini-2.5-pro
```

---

## Security Best Practices

### For Hackathon (Quick & Dirty)
✅ Use ACCOUNTADMIN role
✅ Use your personal credentials
✅ Commit `.env` to `.gitignore` (already done)

### For Production (Later)
- Create dedicated service account user
- Use least-privilege role (not ACCOUNTADMIN)
- Use environment variables or secret manager
- Enable multi-factor authentication
- Rotate credentials regularly

---

## Quick Test Script

After setup, test with:

```bash
python << 'EOF'
import snowflake.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE')
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_VERSION()")
    version = cursor.fetchone()[0]
    
    print(f"✅ Connected to Snowflake!")
    print(f"Version: {version}")
    
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
EOF
```

---

## Cost Optimization Tips

1. **Auto-suspend** is enabled (5 min idle = auto-stop)
2. **Start with SMALL** warehouse (we did this)
3. **Upgrade only if needed** (system auto-suggests)
4. **Monitor credits** in Snowflake UI → Admin → Usage
5. **Development rule**: Suspend when done for the day

---

## Ready to Go!

Once your `.env` is filled out:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test connection
python main.py

# 3. Should see:
# 🔵 Using REAL Snowflake connector
# ✅ Successfully connected to Snowflake

# 4. Test with example data
curl -X POST http://localhost:8000/api/v1/upload \
  -F "dataset1=@examples/dataset1_customers.csv" \
  -F "dataset2=@examples/dataset2_clients.csv"
```

**Your Snowflake is ready for the hackathon!** ❄️🚀

