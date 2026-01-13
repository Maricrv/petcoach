# petcoach

## Backend (FastAPI)

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### Run

```bash
uvicorn backend.main:app --reload
```

## Frontend (Vite + React)

### Setup

```bash
cd frontend
npm install
```

### Run

```bash
npm run dev
```

## Run frontend + backend together

1. Terminal 1: start the backend API.
   ```bash
   uvicorn backend.main:app --reload
   ```
2. Terminal 2: start the Vite frontend.
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
3. Open the frontend at `http://localhost:5173` and submit the form to call
   `http://localhost:8000/next-action`.

### Example request

```bash
curl -X POST http://127.0.0.1:8000/next-action \
  -H "Content-Type: application/json" \
  -d '{
    "weeks": 12,
    "time_of_day": "day",
    "last_activity_minutes_ago": 90,
    "mood": "calm",
    "notes": "Just finished a walk and they are pacing."
  }'
```
