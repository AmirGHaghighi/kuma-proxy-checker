import asyncio
import logging
import ssl
from typing import TYPE_CHECKING, Any

from aiohttp import web

from .constants import HEALTH_SHUTDOWN_TIMEOUT, MAX_BODY_SIZE
from .templates import TEMPLATE_PATTERN, TEMPLATE_VARIABLES

if TYPE_CHECKING:
    from .config import HealthCheckConfig

logger = logging.getLogger("proxy-monitor.health")


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

    app = web.Application(client_max_size=MAX_BODY_SIZE)
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
        shutdown_timeout=HEALTH_SHUTDOWN_TIMEOUT,
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
