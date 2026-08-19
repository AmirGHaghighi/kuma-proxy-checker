from .models import Status


class StatusFormatter:
    """Centralized status message formatting for consistent log output."""

    @staticmethod
    def format(
        level: Status,
        identifier: str,
        message: str,
        ping: int | None = None,
    ) -> str:
        """Format a status message with optional ping time."""
        ping_str = f" ({ping}ms)" if ping is not None else ""
        return f"{level.value} : {identifier} : {message}{ping_str}"

    @staticmethod
    def ok(identifier: str, ping: int) -> str:
        """Format an OK status message."""
        return StatusFormatter.format(Status.OK, identifier, "OK", ping)

    @staticmethod
    def failed(identifier: str, proxy: str, attempt: int, total: int) -> str:
        """Format a FAILED status message."""
        return StatusFormatter.format(
            Status.FAILED, identifier, f"Proxy failed '{proxy}' ({attempt}/{total})"
        )

    @staticmethod
    def error(identifier: str, error: str) -> str:
        """Format an ERROR status message."""
        return StatusFormatter.format(Status.ERROR, identifier, error)

    @staticmethod
    def failed_after_retries(identifier: str, proxy: str) -> str:
        """Format a final FAILED status after all retries exhausted."""
        return StatusFormatter.format(
            Status.FAILED, identifier, f"Proxy failed after retries: {proxy}"
        )
