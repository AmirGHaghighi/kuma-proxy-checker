import argparse
import asyncio
import json
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple
from urllib.parse import urlparse
import time

import httpx


# -------------------------
# Models
# -------------------------

@dataclass
class ProxyTarget:
    proxy: str
    push_url: str
    remark: Optional[str] = None


@dataclass
class AppConfig:
    test_url: str
    expected_status: int
    retries: int
    timeout_seconds: float
    retry_delay_seconds: float
    interval_minutes: int
    targets: List[ProxyTarget]


# -------------------------
# Logging
# -------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("proxy-monitor")


# -------------------------
# Config Loading
# -------------------------

ALLOWED_PROXY_SCHEMES = {
    "http",
    "https",
    "socks4",
    "socks5",
    "socks5h",
}


def validate_proxy_url(proxy: str):
    parsed = urlparse(proxy)
    if parsed.scheme.lower() not in ALLOWED_PROXY_SCHEMES:
        raise ValueError(f"Unsupported proxy scheme: {proxy}")


def load_config(path: str) -> AppConfig:
    with open(path, "r") as f:
        raw = json.load(f)

    required = [
        "test_url",
        "expected_status",
        "retries",
        "timeout_seconds",
        "retry_delay_seconds",
        "interval_minutes",
        "targets",
    ]

    for key in required:
        if key not in raw:
            raise ValueError(f"Missing config field: {key}")

    targets: List[ProxyTarget] = []
    for item in raw["targets"]:
        if "proxy" not in item or "push_url" not in item:
            raise ValueError("Each target must contain proxy and push_url")

        validate_proxy_url(item["proxy"])
        remark = item.get("remark")
        if remark is not None and str(remark).strip() == "":
            remark = None
        targets.append(ProxyTarget(
            proxy=item["proxy"],
            push_url=item["push_url"],
            remark=remark,
        ))

    if not targets:
        raise ValueError("No targets defined")

    return AppConfig(
        test_url=raw["test_url"],
        expected_status=int(raw["expected_status"]),
        retries=int(raw["retries"]),
        timeout_seconds=float(raw["timeout_seconds"]),
        retry_delay_seconds=float(raw["retry_delay_seconds"]),
        interval_minutes=int(raw["interval_minutes"]),
        targets=targets,
    )


# -------------------------
# Proxy Tester
# -------------------------

class ProxyTester:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg

    async def test_once(self, proxy: str) -> Tuple[bool, Optional[int], Optional[str]]:
        try:
            start = time.perf_counter()
            async with httpx.AsyncClient(
                proxy=proxy,
                timeout=self.cfg.timeout_seconds,
                follow_redirects=True,
            ) as client:
                r = await client.get(self.cfg.test_url)
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                if r.status_code == self.cfg.expected_status:
                    return True, elapsed_ms, None
                return False, None, None

        except Exception as e:
            logger.debug("Proxy error %s → %s", proxy, e)
            return False, None, str(e)

    async def test_with_retries(self, proxy: str, name: str) -> Tuple[bool, Optional[int], Optional[str]]:
        for attempt in range(1, self.cfg.retries + 1):
            ok, ping, err = await self.test_once(proxy)

            if err is not None:
                # Log as: ERROR : Remark : message
                logger.error("ERROR : %s → %s", name, err)
                return False, None, str(err)

            if ok:
                # Log as: OK : Remark : message (include proxy and ping for context)
                logger.info("OK : %s → Proxy OK %s (attempt %d) ping=%sms", name, proxy, attempt, ping)
                return True, ping, "OK"

            # Intermediate failure
            logger.warning(
                "FAILED : %s : Proxy failed %s (%d/%d)",
                name,
                proxy,
                attempt,
                self.cfg.retries,
            )

            if attempt < self.cfg.retries:
                await asyncio.sleep(self.cfg.retry_delay_seconds)

        logger.error("FAILED : %s : Proxy failed after retries %s", name, proxy)
        return False, None, "FAILED"


# -------------------------
# Notifier
# -------------------------

class UptimeKumaNotifier:
    async def send(self, push_url: str, status: str, message: str, ping: Optional[int] = None):
        params = {
            "status": status,
            "msg": message,
            "ping": ping if ping is not None else "",
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(push_url, params=params)
                r.raise_for_status()
                logger.info("Push sent → %s", status)

        except Exception as e:
            logger.error("Push failed → %s", e)


# -------------------------
# App
# -------------------------

class ProxyMonitorApp:
    def __init__(self, cfg: AppConfig, run_once: bool):
        self.cfg = cfg
        self.run_once = run_once
        self.tester = ProxyTester(cfg)
        self.notifier = UptimeKumaNotifier()

    async def check_target(self, target: ProxyTarget):
        identifier = target.remark if (target.remark and str(target.remark).strip()) else target.proxy

        ok, ping, message = await self.tester.test_with_retries(target.proxy, identifier)

        if ok:
            # Include ping in the message like: "OK : Remark : OK (950 ms)"
            ping_str = f"{ping} ms" if ping is not None else ""
            final_message = f"OK : {identifier} : OK ({ping_str})"
        else:
            if message == "FAILED":
                final_message = f"FAILED : {identifier} : FAILED"
            else:
                # error case - message contains the error text
                final_message = f"ERROR : {identifier} : {message}"

        status = "up" if ok else "down"

        await self.notifier.send(target.push_url, status, final_message, ping if ok else None)

    async def run_cycle(self):
        await asyncio.gather(
            *(self.check_target(t) for t in self.cfg.targets)
        )

    async def run(self):
        while True:
            logger.info("Starting check cycle")
            await self.run_cycle()

            if self.run_once or self.cfg.interval_minutes <= 0:
                break

            sleep_s = self.cfg.interval_minutes * 60
            logger.info("Sleeping %d minutes", self.cfg.interval_minutes)
            await asyncio.sleep(sleep_s)


# -------------------------
# CLI
# -------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="proxy-monitor",
        description="Proxy health checker with per-proxy Uptime Kuma push reporting",
    )

    p.add_argument(
        "-c",
        "--config",
        required=True,
        help="Path to config.json",
    )

    p.add_argument(
        "--once",
        action="store_true",
        help="Run only one check cycle",
    )

    return p


# -------------------------
# Entry
# -------------------------

def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    cfg = load_config(args.config)
    app = ProxyMonitorApp(cfg, run_once=args.once)

    asyncio.run(app.run())


if __name__ == "__main__":
    main()
