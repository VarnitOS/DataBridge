#!/bin/bash
# Start server for demos (with auto-reload disabled to preserve sessions)

echo "🚀 Starting EY Data Integration SaaS Server..."
echo "=================================================="
echo ""

# Kill any existing server
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Start server WITHOUT auto-reload (so sessions persist in memory)
export DEBUG=False

python3 -c "
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from api.routes import router as api_router
from api.websocket import router as ws_router
from core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description='AI-powered data integration platform for EY',
    docs_url='/docs',
    redoc_url='/redoc'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(api_router)
app.include_router(ws_router, prefix='/api/v1')

@app.get('/')
async def root():
    return {
        'app': settings.APP_NAME,
        'version': settings.APP_VERSION,
        'status': 'running',
        'docs': '/docs',
        'health': '/api/v1/health'
    }

print('✅ Server started!')
print('📖 API Docs: http://localhost:8000/docs')
print('🔌 WebSocket ready for agent monitoring')
print('Press CTRL+C to stop')
print('')

uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
"
