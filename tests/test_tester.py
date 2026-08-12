from unittest.mock import AsyncMock, patch

import pytest

from kuma_proxy_checker.tester import ProxyTester


@pytest.fixture
def tester():
    return ProxyTester(
        test_url="http://example.com",
        expected_status=200,
        timeout_seconds=5.0,
        retries=3,
        retry_delay_seconds=0.01,
    )


@pytest.mark.asyncio
async def test_test_once_success(tester):
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        ok, ping, err = await tester.test_once("http://proxy:8080")
        assert ok is True
        assert ping is not None
        assert err is None


@pytest.mark.asyncio
async def test_test_once_wrong_status(tester):
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        ok, ping, err = await tester.test_once("http://proxy:8080")
        assert ok is False
        assert "Unexpected status" in err


@pytest.mark.asyncio
async def test_test_with_retries_eventually_succeeds(tester):
    with patch("httpx.AsyncClient") as mock_client:
        mock_response_fail = AsyncMock()
        mock_response_fail.status_code = 500
        mock_response_ok = AsyncMock()
        mock_response_ok.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_ok,
        ]

        ok, ping, msg = await tester.test_with_retries("http://proxy:8080", "test-proxy")
        assert ok is True
        assert msg == "OK"
