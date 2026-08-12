from importlib.metadata import version

from .app import ProxyMonitorApp
from .config import AppConfig, ProxyTarget
from .models import ProxyScheme, Status
from .notifier import NotifierProtocol, UptimeKumaNotifier
from .tester import ProxyTester

__version__ = version("kuma-proxy-checker")

__all__ = [
    "AppConfig",
    "ProxyTarget",
    "Status",
    "ProxyScheme",
    "ProxyMonitorApp",
    "ProxyTester",
    "UptimeKumaNotifier",
    "NotifierProtocol",
    "__version__",
]
