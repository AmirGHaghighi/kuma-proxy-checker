import pytest

from kuma_proxy_checker.config import AppConfig, ProxyTarget


def test_valid_config_loads(sample_config):
    assert len(sample_config.targets) == 2
    assert str(sample_config.targets[1].proxy) == "socks5://user:pass@proxy2:1080"


def test_invalid_proxy_scheme_rejected():
    with pytest.raises(Exception):
        ProxyTarget(proxy="ftp://invalid.com", push_url="http://kuma/push")


def test_empty_targets_rejected():
    with pytest.raises(Exception):
        AppConfig(
            test_url="http://example.com",
            expected_status=200,
            targets=[],
        )


def test_missing_required_field_rejected():
    with pytest.raises(Exception):
        AppConfig(test_url="http://example.com")
