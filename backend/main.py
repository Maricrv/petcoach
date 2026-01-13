"""PetCoach backend entry point."""

from datetime import datetime, time, timedelta, timezone
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal

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
    session_id: str | None = Field(
        default=None, description="Optional session id for lightweight memory."
    )


class NextActionResponse(BaseModel):
    action: str
    reason: str
    what_to_avoid: str
    reassurance: str
    next_check_in_minutes: int
    stage: str
    scenario: str


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


SESSION_MEMORY: dict[str, dict[str, object]] = {}
SESSION_TTL = timedelta(minutes=60)


@app.post("/next-action", response_model=NextActionResponse)
def next_action(payload: NextActionRequest) -> NextActionResponse:
    stage = _stage_from_age(payload.puppy_age_weeks)

    if payload.puppy_age_weeks < 16 and payload.hours_since_last_potty >= 1:
        return NextActionResponse(
            action="Take your puppy outside for a potty break.",
            reason="Young puppies need frequent potty breaks, especially every 1-2 hours.",
            next_check_in_minutes=30,
            stage=stage,
            scenario="potty",
        )

    if payload.hours_since_last_meal >= 5 and not is_nighttime:
        return NextActionResponse(
            action="Offer a meal or snack.",
            reason="Puppies typically need meals every 4-6 hours during the day.",
            next_check_in_minutes=60,
            stage=stage,
            scenario="meal",
        )

    if is_nighttime:
        return NextActionResponse(
            action="Settle your puppy for sleep in their crate.",
            reason="Nighttime is for rest; keep stimulation low and lights dim.",
            next_check_in_minutes=120,
            stage=stage,
            scenario="overtired",
        )

    return NextActionResponse(
        action=action,
        reason=reason,
        next_check_in_minutes=next_check_in_minutes,
        stage=stage,
        scenario="owner_overwhelmed",
    )


def _stage_from_age(age_weeks: int) -> str:
    if age_weeks <= 12:
        return "Early puppy"
    if age_weeks <= 24:
        return "Growing puppy"
    if age_weeks <= 52:
        return "Adolescent"
    return "Adult"


def _scenario_from_inputs(
    *,
    age_weeks: int,
    hours_since_last_potty: float,
    hours_since_last_meal: float,
    is_nighttime: bool,
) -> str:
    if age_weeks < 16 and hours_since_last_potty >= 1:
        return "potty_break"
    if hours_since_last_meal >= 5 and not is_nighttime:
        return "meal_time"
    if is_nighttime:
        return "sleep_time"
    return "play_time"


def _should_use_plan_b(session_id: str, scenario: str) -> bool:
    previous = SESSION_MEMORY.get(session_id)
    if not previous:
        return False
    timestamp = previous.get("timestamp")
    if not isinstance(timestamp, datetime):
        return False
    if datetime.now(timezone.utc) - timestamp > SESSION_TTL:
        return False
    return previous.get("scenario") == scenario


def _action_for_scenario(scenario: str, *, use_plan_b: bool) -> tuple[str, str, int]:
    plan_a = {
        "potty_break": (
            "Take your puppy outside for a potty break.",
            "Young puppies need frequent potty breaks, especially every 1-2 hours.",
            30,
        ),
        "meal_time": (
            "Offer a meal or snack.",
            "Puppies typically need meals every 4-6 hours during the day.",
            60,
        ),
        "sleep_time": (
            "Settle your puppy for sleep in their crate.",
            "Nighttime is for rest; keep stimulation low and lights dim.",
            120,
        ),
        "play_time": (
            "Provide a short play or training session.",
            "If basic needs are met, a brief activity helps with bonding and learning.",
            45,
        ),
    }
    plan_b = {
        "potty_break": (
            "Try a different potty spot or a short leash walk outside (Plan B). "
            "We're trying a different approach to see if it helps.",
            "A change of scenery can help a puppy relax and go potty.",
            30,
        ),
        "meal_time": (
            "Offer a small portion or use a puzzle feeder (Plan B). "
            "We're trying a different approach to keep things engaging.",
            "A lighter or interactive meal can be easier if appetite is low.",
            60,
        ),
        "sleep_time": (
            "Dim the room and add a soft white-noise cue (Plan B). "
            "We're trying a different approach to encourage settling.",
            "Consistent cues can help a puppy wind down at night.",
            120,
        ),
        "play_time": (
            "Swap in a calm enrichment game like a sniff-and-find (Plan B). "
            "We're trying a different approach for variety.",
            "Low-key enrichment still builds skills without over-stimulation.",
            45,
        ),
    }
    if use_plan_b:
        return plan_b[scenario]
    return plan_a[scenario]
