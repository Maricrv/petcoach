"""PetCoach backend entry point."""

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
    time_of_day: Literal["morning", "afternoon", "evening", "night"]
    last_activity_minutes_ago: int = Field(..., ge=0)
    notes: str = Field("", description="Short notes about what you're seeing.")
    mood: Literal["calm", "chaotic", "overwhelmed"] = "calm"


class NextActionResponse(BaseModel):
    action: str
    reason: str
    what_to_avoid: str
    reassurance: str
    next_check_in_minutes: int
    stage: str
    scenario: Literal[
        "potty",
        "overtired",
        "biting",
        "barking",
        "crate",
        "owner_overwhelmed",
        "default",
    ]
    disclaimer: str


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/next-action", response_model=NextActionResponse)
def next_action(payload: NextActionRequest) -> NextActionResponse:
    stage = _stage_from_age(payload.puppy_age_weeks)
    scenario, response = _decision_engine(payload)

    return NextActionResponse(
        action=response["action"],
        reason=response["reason"],
        what_to_avoid=response["what_to_avoid"],
        reassurance=response["reassurance"],
        next_check_in_minutes=response["next_check_in_minutes"],
        stage=stage,
        scenario=scenario,
        disclaimer=response["disclaimer"],
    )


def _stage_from_age(age_weeks: int) -> str:
    if age_weeks <= 12:
        return "Early puppy"
    if age_weeks <= 24:
        return "Growing puppy"
    if age_weeks <= 52:
        return "Adolescent"
    return "Adult"


def _decision_engine(payload: NextActionRequest) -> tuple[str, dict[str, str | int]]:
    notes = payload.notes.lower()
    disclaimer = "If anything feels urgent or unsafe, contact a vet or trainer."

    health_flags = ("vomit", "diarrhea", "blood", "injury", "poison", "seizure")
    has_health_concern = any(flag in notes for flag in health_flags)

    scenarios = {
        "owner_overwhelmed": payload.mood == "overwhelmed"
        or any(term in notes for term in ("overwhelmed", "frustrated", "superada")),
        "overtired": payload.puppy_age_weeks <= 16
        and payload.time_of_day in ("evening", "night")
        and payload.last_activity_minutes_ago <= 20,
        "potty": payload.puppy_age_weeks <= 16
        and payload.last_activity_minutes_ago >= 45,
        "crate": any(term in notes for term in ("crate", "jaula", "cry", "llora")),
        "biting": payload.puppy_age_weeks <= 16
        and any(term in notes for term in ("bite", "mord", "muerde")),
        "barking": any(term in notes for term in ("bark", "ladra", "ladr")),
    }

    if scenarios["owner_overwhelmed"]:
        return (
            "owner_overwhelmed",
            {
                "action": "Take a 2-minute reset: breathe, sip water, and step back.",
                "reason": "Your calm helps your puppy settle too.",
                "what_to_avoid": "Avoid doing too much at once or raising your voice.",
                "reassurance": "You’re doing your best, and this phase gets easier.",
                "next_check_in_minutes": 5,
                "disclaimer": disclaimer,
            },
        )

    if has_health_concern:
        return (
            "default",
            {
                "action": "Pause and assess your puppy’s health and safety first.",
                "reason": "Some notes sound like they could be health-related.",
                "what_to_avoid": "Avoid waiting if symptoms worsen or seem severe.",
                "reassurance": "It’s okay to ask for help when you’re unsure.",
                "next_check_in_minutes": 15,
                "disclaimer": disclaimer,
            },
        )

    if scenarios["overtired"]:
        return (
            "overtired",
            {
                "action": "Offer a calm wind-down and a short nap.",
                "reason": "Young puppies often get extra cranky when tired.",
                "what_to_avoid": "Avoid high-energy play right now.",
                "reassurance": "A quick rest usually helps a lot.",
                "next_check_in_minutes": 30,
                "disclaimer": disclaimer,
            },
        )

    if scenarios["potty"]:
        return (
            "potty",
            {
                "action": "Take your puppy out for a potty break.",
                "reason": "Young puppies need frequent potty trips.",
                "what_to_avoid": "Avoid waiting too long after signs of restlessness.",
                "reassurance": "Accidents happen—this is normal.",
                "next_check_in_minutes": 20,
                "disclaimer": disclaimer,
            },
        )

    if scenarios["crate"]:
        return (
            "crate",
            {
                "action": "Make the crate cozy and add a quiet chew.",
                "reason": "Crying often means they need comfort or a short reset.",
                "what_to_avoid": "Avoid sudden loud noises or long isolation.",
                "reassurance": "Crate comfort builds over time.",
                "next_check_in_minutes": 15,
                "disclaimer": disclaimer,
            },
        )

    if scenarios["biting"]:
        return (
            "biting",
            {
                "action": "Swap to a chew toy and end play for 30 seconds.",
                "reason": "Puppies explore with their mouths when excited.",
                "what_to_avoid": "Avoid yelling or rough play that ramps them up.",
                "reassurance": "This phase is common and will improve.",
                "next_check_in_minutes": 15,
                "disclaimer": disclaimer,
            },
        )

    if scenarios["barking"]:
        return (
            "barking",
            {
                "action": "Pause, wait for quiet, then reward a calm moment.",
                "reason": "Barking often means they want attention or are alerting.",
                "what_to_avoid": "Avoid accidentally rewarding the barking.",
                "reassurance": "Small calm moments add up fast.",
                "next_check_in_minutes": 20,
                "disclaimer": disclaimer,
            },
        )

    return (
        "default",
        {
            "action": "Try a short, calm play or training game.",
            "reason": "A little structure helps puppies feel secure.",
            "what_to_avoid": "Avoid long sessions that feel overwhelming.",
            "reassurance": "You’re building good habits one step at a time.",
            "next_check_in_minutes": 30,
            "disclaimer": disclaimer,
        },
    )
