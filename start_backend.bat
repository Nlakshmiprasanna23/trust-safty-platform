@echo off
cd backend
python -m venv .venv 2>nul
call .venv\Scripts\activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8000
