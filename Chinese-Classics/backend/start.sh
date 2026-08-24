#!/bin/bash
# Start script for backend

cd "$(dirname "$0")"

export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-a9375f14d4a6496dab811cc8d2faf92f}"

source venv/bin/activate

exec python3 -c "
import uvicorn
from app.main import app
uvicorn.run(app, host='0.0.0.0', port=8000, reload=False, log_level='info')
"
