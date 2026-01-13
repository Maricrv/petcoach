from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_next_action_selects_potty_scenario():
    response = client.post(
        "/next-action",
        json={
            "puppy_age_weeks": 12,
            "hours_since_last_potty": 1.5,
            "hours_since_last_meal": 2,
            "local_time": "10:00",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["scenario"] == "potty"
    assert "potty" in data["action"].lower()


def test_next_action_selects_overtired_scenario():
    response = client.post(
        "/next-action",
        json={
            "puppy_age_weeks": 20,
            "hours_since_last_potty": 0.5,
            "hours_since_last_meal": 2,
            "local_time": "23:15",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["scenario"] == "overtired"
    assert "sleep" in data["action"].lower()


def test_next_action_selects_owner_overwhelmed_scenario():
    response = client.post(
        "/next-action",
        json={
            "puppy_age_weeks": 20,
            "hours_since_last_potty": 0.5,
            "hours_since_last_meal": 2,
            "local_time": "14:00",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["scenario"] == "owner_overwhelmed"
    assert "play" in data["action"].lower()
