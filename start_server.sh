#!/bin/bash
# Start server script - ensures venv is activated

cd "$(dirname "$0")"
source .venv/bin/activate
uvicorn app:app --reload
