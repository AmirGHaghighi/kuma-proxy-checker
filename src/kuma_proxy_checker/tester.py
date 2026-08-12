import asyncio
import logging
import time

import httpx

from .logging_utils import fmt_log
from .models import Status

logger = logging.getLogger("proxy-monitor.tester")


class ProxyTester:
    def __init__(
        self,
        test_url: str,
        expected_status: int,
        timeout_seconds: float,
        retries: int,
        retry_delay_seconds: float,
    ):
        self.test_url = test_url
        self.expected_status = expected_status
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds

    async def test_once(self, proxy: str) -> tuple[bool, int | None, str | None]:
        try:
            start = time.perf_counter()
            async with httpx.AsyncClient(
                proxy=proxy,
                timeout=self.timeout_seconds,
                follow_redirects=True,
            ) as client:
                r = await client.get(self.test_url)
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                if r.status_code == self.expected_status:
                    return True, elapsed_ms, None
                return False, None, f"Unexpected status code: {r.status_code}"
        except Exception as e:
            logger.debug("Proxy error %s \u2192 %s", proxy, e)
            return False, None, f"{e.__class__.__name__}: {e}"

    async def test_with_retries(
        self, proxy: str, identifier: str
    ) -> tuple[bool, int | None, str | None]:
        last_err_msg = None
        for attempt in range(1, self.retries + 1):
            logger.info("Testing proxy: %s (attempt %d/%d)", proxy, attempt, self.retries)
            ok, ping, err = await self.test_once(proxy)

            if ok:
                logger.info(fmt_log(Status.OK, identifier, "OK", ping))
                return True, ping, "OK"

            if err:
                logger.error(fmt_log(Status.ERROR, identifier, err))
                last_err_msg = err

            logger.warning(
                fmt_log(
                    Status.FAILED, identifier, f"Proxy failed '{proxy}' ({attempt}/{self.retries})"
                )
            )

            if attempt < self.retries:
                await asyncio.sleep(self.retry_delay_seconds)

        logger.error(fmt_log(Status.FAILED, identifier, f"Proxy failed after retries: {proxy}"))
        return False, None, last_err_msg or "FAILED"
