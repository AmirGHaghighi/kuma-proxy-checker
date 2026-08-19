import logging
from typing import Protocol

from .http_client import create_http_client
from .models import Status

logger = logging.getLogger("proxy-monitor.notifier")


class NotifierProtocol(Protocol):
    async def send(
        self,
        push_url: str,
        status: Status,
        message: str,
        ping: int | None = None,
    ) -> None: ...


class UptimeKumaNotifier:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def send(
        self,
        push_url: str,
        status: Status,
        message: str,
        ping: int | None = None,
    ) -> None:
        params = {"status": status.value, "msg": message, "ping": ping if ping is not None else ""}
        try:
            async with create_http_client(timeout=self.timeout) as client:
                r = await client.get(push_url, params=params)
                r.raise_for_status()
            logger.info("Push sent \u2192 %s", status.value)
        except Exception as e:
            logger.error("Push failed \u2192 %s", e)
