"""PetCoach backend entry point."""

from datetime import datetime, time, timedelta, timezone
from uuid import uuid4

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
    session_id: str | None = Field(
        default=None, description="Optional session id for lightweight memory."
    )


class NextActionResponse(BaseModel):
    action: str
    reason: str
    next_check_in_minutes: int
    stage: str
    session_id: str


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


SESSION_MEMORY: dict[str, dict[str, object]] = {}
SESSION_TTL = timedelta(minutes=60)


@app.post("/next-action", response_model=NextActionResponse)
def next_action(payload: NextActionRequest) -> NextActionResponse:
    current_time = time.fromisoformat(payload.local_time)
    is_nighttime = current_time.hour >= 22 or current_time.hour < 6
    stage = _stage_from_age(payload.puppy_age_weeks)
    session_id = payload.session_id or str(uuid4())

    scenario = _scenario_from_inputs(
        age_weeks=payload.puppy_age_weeks,
        hours_since_last_potty=payload.hours_since_last_potty,
        hours_since_last_meal=payload.hours_since_last_meal,
        is_nighttime=is_nighttime,
    )
    use_plan_b = _should_use_plan_b(session_id, scenario)
    action, reason, next_check_in_minutes = _action_for_scenario(
        scenario, use_plan_b=use_plan_b
    )
    SESSION_MEMORY[session_id] = {
        "scenario": scenario,
        "timestamp": datetime.now(timezone.utc),
    }

    return NextActionResponse(
        action=action,
        reason=reason,
        next_check_in_minutes=next_check_in_minutes,
        stage=stage,
        session_id=session_id,
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
