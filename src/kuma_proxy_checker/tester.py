import asyncio
import logging
import time

from .http_client import create_http_client
from .status_formatter import StatusFormatter
from .tester_config import TesterConfig

logger = logging.getLogger("proxy-monitor.tester")


class ProxyTester:
    def __init__(self, config: TesterConfig):
        self.config = config

    async def test_once(
        self, proxy: str, test_url: str | None = None
    ) -> tuple[bool, int | None, str | None]:
        try:
            start = time.perf_counter()
            async with create_http_client(
                timeout=self.config.timeout_seconds,
                proxy=proxy,
                follow_redirects=True,
            ) as client:
                r = await client.get(test_url or self.config.test_url)
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                if r.status_code == self.config.expected_status:
                    return True, elapsed_ms, None
                return False, None, f"Unexpected status code: {r.status_code}"
        except Exception as e:
            logger.debug("Proxy error %s \u2192 %s", proxy, e)
            return False, None, f"{e.__class__.__name__}: {e}"

    async def test_with_retries(
        self, proxy: str, identifier: str, test_url: str | None = None
    ) -> tuple[bool, int | None, str | None]:
        last_err_msg = None
        for attempt in range(1, self.config.retries + 1):
            logger.info("Testing proxy: %s (attempt %d/%d)", proxy, attempt, self.config.retries)
            ok, ping, err = await self.test_once(proxy, test_url=test_url)

            if ok:
                logger.info(StatusFormatter.ok(identifier, ping))
                return True, ping, "OK"

            if err:
                logger.error(StatusFormatter.error(identifier, err))
                last_err_msg = err

            logger.warning(
                StatusFormatter.failed(identifier, proxy, attempt, self.config.retries)
            )

            if attempt < self.config.retries:
                await asyncio.sleep(self.config.retry_delay_seconds)

        logger.error(StatusFormatter.failed_after_retries(identifier, proxy))
        return False, None, last_err_msg or "FAILED"
