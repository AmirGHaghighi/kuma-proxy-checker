from unittest.mock import AsyncMock, patch

import pytest

from kuma_proxy_checker.models import Status
from kuma_proxy_checker.notifier import UptimeKumaNotifier


@pytest.mark.asyncio
async def test_notifier_send_success():
    notifier = UptimeKumaNotifier()
    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.get = AsyncMock()
        mock_client.return_value = mock_client_instance
        await notifier.send("http://kuma/push", Status.UP, "OK", 100)
        mock_client_instance.get.assert_called_once()


@pytest.mark.asyncio
async def test_notifier_send_failure_logs_error(caplog):
    notifier = UptimeKumaNotifier()
    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.get = AsyncMock(side_effect=Exception("network error"))
        mock_client.return_value = mock_client_instance
        await notifier.send("http://kuma/push", Status.DOWN, "FAILED")
        assert "Push failed" in caplog.text
