from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.config import settings


def test_trigger_requires_auth(client: TestClient) -> None:
    response = client.post(f"{settings.API_V1_STR}/notifications/trigger")
    assert response.status_code == 401


def test_trigger_returns_result(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    with patch(
        "app.domains.notifications.service.ntfy_client.NtfyClient.send",
        new_callable=AsyncMock,
        return_value=True,
    ):
        response = client.post(
            f"{settings.API_V1_STR}/notifications/trigger",
            headers=normal_user_token_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert "statements_found" in data
    assert "notification_sent" in data
    assert isinstance(data["statements_found"], int)
    assert isinstance(data["notification_sent"], bool)
