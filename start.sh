#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Initialize database
python -m surgeonmatch.db.init_db

# Start the FastAPI server
uvicorn surgeonmatch.main:app --reload --host 0.0.0.0 --port 8000
