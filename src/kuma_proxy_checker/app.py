import asyncio
import logging
import signal

from .config import AppConfig, ProxyTarget
from .health import run_health_server
from .logging_utils import get_identifier
from .models import Status
from .notifier import NotifierProtocol, UptimeKumaNotifier
from .status_formatter import StatusFormatter
from .tester import ProxyTester
from .tester_config import TesterConfig

logger = logging.getLogger("proxy-monitor.app")


class ProxyMonitorApp:
    def __init__(
        self,
        cfg: AppConfig,
        notifier: NotifierProtocol | None = None,
        tester: ProxyTester | None = None,
    ):
        self.cfg = cfg
        self.notifier = notifier or UptimeKumaNotifier(timeout=cfg.notifier_timeout_seconds)
        self.tester = tester or ProxyTester(
            TesterConfig(
                test_url=str(cfg.test_url),
                expected_status=cfg.expected_status,
                timeout_seconds=cfg.timeout_seconds,
                retries=cfg.retries,
                retry_delay_seconds=cfg.retry_delay_seconds,
            )
        )
        self._shutdown = asyncio.Event()
        self._health_task: asyncio.Task | None = None
        self._setup_signals()

    def _setup_signals(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._shutdown.set)
            except NotImplementedError:
                pass

    async def check_target(self, target: ProxyTarget) -> None:
        identifier = get_identifier(target)
        ok, ping, message = await self.tester.test_with_retries(str(target.proxy), identifier)

        if ok:
            final_message = StatusFormatter.ok(identifier, ping)
        else:
            if message == "FAILED":
                final_message = StatusFormatter.format(Status.FAILED, identifier, "FAILED")
            else:
                final_message = StatusFormatter.error(identifier, message)

        status = Status.UP if ok else Status.DOWN
        await self.notifier.send(str(target.push_url), status, final_message, ping if ok else None)

    async def run_cycle(self) -> None:
        await asyncio.gather(*(self.check_target(t) for t in self.cfg.targets))

    async def run(self, run_once: bool = False) -> None:
        if self.cfg.health_check.enabled:
            self._health_task = asyncio.create_task(
                run_health_server(self.cfg.health_check, self._shutdown)
            )
        try:
            while not self._shutdown.is_set():
                logger.info("Starting check cycle")
                await self.run_cycle()

                if run_once or self.cfg.interval_minutes <= 0:
                    break

                sleep_s = self.cfg.interval_minutes * 60
                logger.info("Sleeping %d minutes", self.cfg.interval_minutes)
                try:
                    await asyncio.wait_for(self._shutdown.wait(), timeout=sleep_s)
                    break
                except TimeoutError:
                    continue
        finally:
            if self._health_task:
                self._health_task.cancel()
                try:
                    await self._health_task
                except asyncio.CancelledError:
                    pass
