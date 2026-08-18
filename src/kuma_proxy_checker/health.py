import asyncio
import logging
import os
import re
import socket
import ssl
import time
from collections.abc import Callable
from importlib.metadata import version
from typing import TYPE_CHECKING, Any

from aiohttp import web

if TYPE_CHECKING:
    from .config import HealthCheckConfig

logger = logging.getLogger("proxy-monitor.health")

__version__ = version("kuma-proxy-checker")

_APP_START_TIME = time.time()

TEMPLATE_VARIABLES: dict[str, Callable[[], Any]] = {
    "uptime_seconds": lambda: time.time() - _APP_START_TIME,
    "timestamp": lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "version": lambda: __version__,
    "hostname": lambda: socket.gethostname(),
    "pid": lambda: os.getpid(),
}

ALLOWED_VAR_NAMES = frozenset(TEMPLATE_VARIABLES.keys())

# Regex to match {variable} format (like Python f-strings but simpler)
TEMPLATE_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def validate_template_vars(obj: Any, path: str = "$") -> None:
    if isinstance(obj, str):
        used = {m.group(1) for m in TEMPLATE_PATTERN.finditer(obj)}
        invalid = used - ALLOWED_VAR_NAMES
        if invalid:
            raise ValueError(
                f"{path}: disallowed template variables: {invalid}. Allowed: {sorted(ALLOWED_VAR_NAMES)}"
            )
    elif isinstance(obj, dict):
        for k, v in obj.items():
            validate_template_vars(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            validate_template_vars(v, f"{path}[{i}]")


def _render_recursive(obj: Any, context: dict) -> Any:
    if isinstance(obj, str):
        return TEMPLATE_PATTERN.sub(lambda m: str(context.get(m.group(1), m.group(0))), obj)
    elif isinstance(obj, dict):
        return {k: _render_recursive(v, context) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_render_recursive(v, context) for v in obj]
    return obj


def render_template(obj: Any) -> Any:
    context = {name: fn() for name, fn in TEMPLATE_VARIABLES.items()}
    return _render_recursive(obj, context)


async def run_health_server(cfg: "HealthCheckConfig", shutdown: asyncio.Event) -> None:
    async def handler(request: web.Request) -> web.Response:
        rendered = render_template(cfg.response_json)
        return web.json_response(rendered, status=cfg.response_code)

    # Remove Server header for security
    async def remove_server_header(request, response):
        response.headers.pop("Server", None)

    app = web.Application(client_max_size=1024)
    app.router.add_get(cfg.path, handler)
    app.on_response_prepare.append(remove_server_header)

    runner = web.AppRunner(app, access_log=None)
    await runner.setup()

    ssl_context = None
    if cfg.ssl_enabled:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(cfg.ssl_certfile, cfg.ssl_keyfile)

    site = web.TCPSite(
        runner,
        cfg.host,
        cfg.port,
        ssl_context=ssl_context,
        shutdown_timeout=2.0,
    )

    await site.start()
    logger.info(
        "Health check server listening on %s://%s:%d%s",
        "https" if cfg.ssl_enabled else "http",
        cfg.host,
        cfg.port,
        cfg.path,
    )

    try:
        await shutdown.wait()
    finally:
        await runner.cleanup()
        logger.info("Health check server stopped")
