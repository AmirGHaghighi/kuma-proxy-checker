from unittest.mock import AsyncMock, MagicMock

import pytest

from kuma_proxy_checker.app import ProxyMonitorApp
from kuma_proxy_checker.config import AppConfig, ProxyTarget


@pytest.fixture
def config():
    return AppConfig(
        test_url="http://example.com",
        expected_status=200,
        retries=1,
        timeout_seconds=1.0,
        retry_delay_seconds=0.01,
        interval_minutes=0,
        targets=[
            ProxyTarget(proxy="http://p1:8080", push_url="http://kuma/1", remark="one"),
            ProxyTarget(proxy="http://p2:8080", push_url="http://kuma/2"),
        ],
    )


@pytest.fixture
def mock_tester():
    tester = MagicMock()
    tester.test_with_retries = AsyncMock(return_value=(True, 50, "OK"))
    return tester


@pytest.fixture
def mock_notifier():
    notifier = MagicMock()
    notifier.send = AsyncMock()
    return notifier


@pytest.mark.asyncio
async def test_run_cycle_calls_all_targets(config, mock_tester, mock_notifier):
    app = ProxyMonitorApp(config, notifier=mock_notifier, tester=mock_tester)
    await app.run_cycle()
    assert mock_tester.test_with_retries.call_count == 2
    assert mock_notifier.send.call_count == 2


@pytest.mark.asyncio
async def test_run_once_exits_after_one_cycle(config, mock_tester, mock_notifier):
    app = ProxyMonitorApp(config, notifier=mock_notifier, tester=mock_tester)
    await app.run(run_once=True)
    assert mock_tester.test_with_retries.call_count == 2


@pytest.mark.asyncio
async def test_interval_zero_exits(config, mock_tester, mock_notifier):
    config.interval_minutes = 0
    app = ProxyMonitorApp(config, notifier=mock_notifier, tester=mock_tester)
    await app.run(run_once=False)
    assert mock_tester.test_with_retries.call_count == 2
