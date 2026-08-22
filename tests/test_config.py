import pytest

from kuma_proxy_checker.config import AppConfig, ProxyTarget


def test_valid_config_loads(sample_config):
    assert len(sample_config.proxy_targets) == 2
    assert str(sample_config.proxy_targets[1].proxy) == "socks5://user:pass@proxy2:1080"


def test_invalid_proxy_scheme_rejected():
    with pytest.raises(Exception):
        ProxyTarget(proxy="ftp://invalid.com", push_url="http://kuma/push")


def test_empty_targets_accepted():
    cfg = AppConfig()
    assert cfg.proxy_targets == []
    assert cfg.expected_status == 200


def test_missing_default_test_url_with_targets_rejected():
    with pytest.raises(Exception, match="default_test_url is required"):
        AppConfig(
            expected_status=200,
            proxy_targets=[ProxyTarget(proxy="http://proxy:8080", push_url="http://kuma/push")],
        )


def test_target_with_custom_test_url():
    target = ProxyTarget(
        proxy="http://proxy:8080",
        push_url="http://kuma/push",
        test_url="https://custom.example.com",
    )
    assert str(target.test_url) == "https://custom.example.com/"


def test_target_without_test_url():
    target = ProxyTarget(proxy="http://proxy:8080", push_url="http://kuma/push")
    assert target.test_url is None


def test_config_with_targets_having_custom_test_url():
    cfg = AppConfig(
        default_test_url="http://default.example.com",
        expected_status=200,
        proxy_targets=[
            ProxyTarget(proxy="http://p1:8080", push_url="http://kuma/1"),
            ProxyTarget(
                proxy="http://p2:8080",
                push_url="http://kuma/2",
                test_url="https://custom.example.com",
            ),
        ],
    )
    assert cfg.proxy_targets[0].test_url is None
    assert str(cfg.proxy_targets[1].test_url) == "https://custom.example.com/"
