from kuma_proxy_checker.config import ProxyTarget
from kuma_proxy_checker.logging_utils import fmt_log, get_identifier
from kuma_proxy_checker.models import Status


def test_fmt_log_with_ping():
    assert fmt_log(Status.OK, "proxy1", "OK", 150) == "OK : proxy1 : OK (150ms)"


def test_fmt_log_without_ping():
    assert fmt_log(Status.ERROR, "proxy1", "timeout") == "ERROR : proxy1 : timeout"


def test_get_identifier_uses_remark():
    target = ProxyTarget(proxy="http://p:8080", push_url="http://kuma", remark="home")
    assert get_identifier(target) == "home"


def test_get_identifier_falls_back_to_proxy():
    target = ProxyTarget(proxy="http://p:8080", push_url="http://kuma", remark="")
    assert get_identifier(target) == "http://p:8080/"


def test_get_identifier_none_remark():
    target = ProxyTarget(proxy="http://p:8080", push_url="http://kuma", remark=None)
    assert get_identifier(target) == "http://p:8080/"
