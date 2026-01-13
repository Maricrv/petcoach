"""PetCoach backend entry point."""

from datetime import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="PetCoach API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NextActionRequest(BaseModel):
    puppy_age_weeks: int = Field(..., ge=6, le=104)
    hours_since_last_potty: float = Field(..., ge=0)
    hours_since_last_meal: float = Field(..., ge=0)
    local_time: str = Field(..., description="Local time in HH:MM (24-hour) format.")


class NextActionResponse(BaseModel):
    action: str
    reason: str
    next_check_in_minutes: int
    stage: str


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/next-action", response_model=NextActionResponse)
def next_action(payload: NextActionRequest) -> NextActionResponse:
    current_time = time.fromisoformat(payload.local_time)
    is_nighttime = current_time.hour >= 22 or current_time.hour < 6
    stage = _stage_from_age(payload.puppy_age_weeks)

    if payload.puppy_age_weeks < 16 and payload.hours_since_last_potty >= 1:
        return NextActionResponse(
            action="Take your puppy outside for a potty break.",
            reason="Young puppies need frequent potty breaks, especially every 1-2 hours.",
            next_check_in_minutes=30,
            stage=stage,
        )

    if payload.hours_since_last_meal >= 5 and not is_nighttime:
        return NextActionResponse(
            action="Offer a meal or snack.",
            reason="Puppies typically need meals every 4-6 hours during the day.",
            next_check_in_minutes=60,
            stage=stage,
        )

    if is_nighttime:
        return NextActionResponse(
            action="Settle your puppy for sleep in their crate.",
            reason="Nighttime is for rest; keep stimulation low and lights dim.",
            next_check_in_minutes=120,
            stage=stage,
        )

    return NextActionResponse(
        action="Provide a short play or training session.",
        reason="If basic needs are met, a brief activity helps with bonding and learning.",
        next_check_in_minutes=45,
        stage=stage,
    )


def _stage_from_age(age_weeks: int) -> str:
    if age_weeks <= 12:
        return "Early puppy"
    if age_weeks <= 24:
        return "Growing puppy"
    if age_weeks <= 52:
        return "Adolescent"
    return "Adult"
