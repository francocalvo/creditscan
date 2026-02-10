from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.domains.notifications.service.ntfy_client import NtfyClient


@pytest.fixture
def client() -> NtfyClient:
    return NtfyClient(server_url="http://ntfy:80")


@pytest.mark.asyncio
async def test_send_success(client: NtfyClient) -> None:
    mock_response = httpx.Response(
        200, json={"id": "abc"}, request=httpx.Request("POST", "http://ntfy:80")
    )
    with patch(
        "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response
    ):
        result = await client.send(
            topic="pf-app-test",
            title="Test Title",
            message="Test message",
            priority=4,
            tags=["credit_card", "warning"],
        )
    assert result is True


@pytest.mark.asyncio
async def test_send_correct_payload(client: NtfyClient) -> None:
    mock_response = httpx.Response(
        200, json={"id": "abc"}, request=httpx.Request("POST", "http://ntfy:80")
    )
    with patch(
        "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response
    ) as mock_post:
        await client.send(
            topic="pf-app-test",
            title="Test Title",
            message="Test message",
            priority=4,
            tags=["credit_card"],
        )
    mock_post.assert_called_once_with(
        "http://ntfy:80",
        json={
            "topic": "pf-app-test",
            "title": "Test Title",
            "message": "Test message",
            "priority": 4,
            "tags": ["credit_card"],
        },
    )


@pytest.mark.asyncio
async def test_send_omits_tags_when_none(client: NtfyClient) -> None:
    mock_response = httpx.Response(
        200, json={"id": "abc"}, request=httpx.Request("POST", "http://ntfy:80")
    )
    with patch(
        "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response
    ) as mock_post:
        await client.send(
            topic="pf-app-test",
            title="Test Title",
            message="Test message",
        )
    call_kwargs = mock_post.call_args
    payload = call_kwargs.kwargs["json"]
    assert "tags" not in payload


@pytest.mark.asyncio
async def test_send_failure_returns_false(client: NtfyClient) -> None:
    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError("connection refused"),
    ):
        result = await client.send(
            topic="pf-app-test",
            title="Test Title",
            message="Test message",
        )
    assert result is False


@pytest.mark.asyncio
async def test_send_http_error_returns_false(client: NtfyClient) -> None:
    mock_response = httpx.Response(500, request=httpx.Request("POST", "http://ntfy:80"))
    with patch(
        "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response
    ):
        result = await client.send(
            topic="pf-app-test",
            title="Test Title",
            message="Test message",
        )
    assert result is False
