import pytest

from kuma_proxy_checker.config import AppConfig, ProxyTarget


@pytest.fixture
def sample_config() -> AppConfig:
    return AppConfig(
        test_url="http://example.com",
        expected_status=200,
        retries=2,
        timeout_seconds=5.0,
        retry_delay_seconds=0.1,
        interval_minutes=0,
        targets=[
            ProxyTarget(proxy="http://proxy1:8080", push_url="http://kuma/push1"),
            ProxyTarget(
                proxy="socks5://user:pass@proxy2:1080", push_url="http://kuma/push2", remark="home"
            ),
        ],
    )
