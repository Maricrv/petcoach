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

### Example request

```bash
curl -X POST http://127.0.0.1:8000/next-action \
  -H "Content-Type: application/json" \
  -d '{
    "puppy_age_weeks": 12,
    "hours_since_last_potty": 1.5,
    "hours_since_last_meal": 4,
    "local_time": "14:30"
  }'
```
