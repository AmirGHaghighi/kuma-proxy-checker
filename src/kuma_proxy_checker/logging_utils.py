import logging

from .config import ProxyTarget
from .models import Status


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def fmt_log(level: Status, identifier: str, message: str, ping: int | None = None) -> str:
    ping_str = f" ({ping}ms)" if ping is not None else ""
    return f"{level.value} : {identifier} : {message}{ping_str}"


def get_identifier(target: ProxyTarget) -> str:
    return target.remark.strip() if target.remark and target.remark.strip() else str(target.proxy)
