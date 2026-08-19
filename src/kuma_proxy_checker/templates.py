import re
import time
from collections.abc import Callable
from importlib.metadata import version
from typing import Any

TEMPLATE_VARIABLES: dict[str, Callable[[], Any]] = {
    "uptime_seconds": lambda: time.time() - _APP_START_TIME,
    "timestamp": lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "version": lambda: version("kuma-proxy-checker"),
    "hostname": lambda: __import__("socket").gethostname(),
    "pid": lambda: __import__("os").getpid(),
}

ALLOWED_VAR_NAMES = frozenset(TEMPLATE_VARIABLES.keys())

TEMPLATE_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

_APP_START_TIME = time.time()
