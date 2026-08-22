from unittest.mock import AsyncMock, MagicMock

import pytest

from kuma_proxy_checker.app import ProxyMonitorApp
from kuma_proxy_checker.config import AppConfig, ProxyTarget


@pytest.fixture
def config():
    return AppConfig(
        default_test_url="http://example.com",
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
    sent_args = [c.args for c in mock_notifier.send.call_args_list]
    assert all(isinstance(url, str) for url, *_ in sent_args)
    assert sent_args[0][0] == "http://kuma/1"


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


@pytest.mark.asyncio
async def test_per_target_test_url_passed(mock_tester, mock_notifier):
    cfg = AppConfig(
        default_test_url="http://default.example.com",
        expected_status=200,
        retries=1,
        timeout_seconds=1.0,
        retry_delay_seconds=0.01,
        interval_minutes=0,
        targets=[
            ProxyTarget(proxy="http://p1:8080", push_url="http://kuma/1"),
            ProxyTarget(
                proxy="http://p2:8080",
                push_url="http://kuma/2",
                test_url="https://custom.example.com",
            ),
        ],
    )
    app = ProxyMonitorApp(cfg, notifier=mock_notifier, tester=mock_tester)
    await app.run_cycle()

    calls = mock_tester.test_with_retries.call_args_list
    assert calls[0].kwargs["test_url"] == "http://default.example.com/"
    assert calls[1].kwargs["test_url"] == "https://custom.example.com/"
