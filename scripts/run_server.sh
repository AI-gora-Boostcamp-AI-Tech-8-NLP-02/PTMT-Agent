#!/bin/bash

# FastAPI 서버 실행 스크립트

echo "Starting FastAPI server..."
cd "$(dirname "$0")/.." || exit
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
