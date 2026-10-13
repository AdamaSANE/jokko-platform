"""Scénario d'intégration du flux échange -> solution -> réputation."""

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _register_and_login(client: TestClient, suffix: str, country: str) -> str:
    payload = {
        "username": f"tester_{suffix}_{uuid.uuid4().hex[:8]}",
        "email": f"{suffix}_{uuid.uuid4().hex[:8]}@test.com",
        "password": "Password123!",
        "display_name": f"Dev {country}",
        "country": country,
        "tech_stack": ["Python", "FastAPI"],
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    response = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_full_exchange_and_karma_workflow() -> None:
    with TestClient(app) as client:
        token_a = _register_and_login(client, "sn", "Sénégal")
        token_b = _register_and_login(client, "ci", "Côte d'Ivoire")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        exchange = client.post(
            "/api/v1/exchanges/",
            json={
                "title": "Configurer CORS sur FastAPI",
                "description": "Mon frontend JavaScript est bloqué par CORS.",
                "language": "python",
                "kind": "problem",
            },
            headers=headers_a,
        )
        assert exchange.status_code == 201, exchange.text
        exchange_id = exchange.json()["id"]

        solution = client.post(
            f"/api/v1/exchanges/{exchange_id}/solutions",
            json={"content": "Ajouter CORSMiddleware avec les origines autorisées."},
            headers=headers_b,
        )
        assert solution.status_code == 201, solution.text
        solution_id = solution.json()["id"]

        solved = client.put(
            f"/api/v1/exchanges/{exchange_id}/solve",
            json={"solution_id": solution_id},
            headers=headers_a,
        )
        assert solved.status_code == 200, solved.text

        leaderboard = client.get("/api/v1/devs/leaderboard", headers=headers_a)
        assert leaderboard.status_code == 200, leaderboard.text
        assert any(entry["impact_score"] >= 10 for entry in leaderboard.json())
