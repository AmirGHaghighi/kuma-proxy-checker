import argparse
import asyncio

from . import __version__
from .app import ProxyMonitorApp
from .config import AppConfig
from .logging_utils import setup_logging


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="proxy-monitor",
        description="Proxy health checker with per-proxy Uptime Kuma push reporting",
    )
    p.add_argument("-c", "--config", required=True, help="Path to config.json")
    p.add_argument("--once", action="store_true", help="Run only one check cycle")
    p.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


async def run_app(config_path: str, once: bool, verbose: bool) -> None:
    setup_logging(verbose)
    cfg = AppConfig.from_file(config_path)
    app = ProxyMonitorApp(cfg)
    await app.run(run_once=once)


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    asyncio.run(run_app(args.config, args.once, args.verbose))


if __name__ == "__main__":
    main()
