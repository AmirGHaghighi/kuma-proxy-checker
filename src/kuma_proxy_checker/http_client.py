import httpx

from .constants import DEFAULT_NOTIFIER_TIMEOUT


def create_http_client(
    timeout: float = DEFAULT_NOTIFIER_TIMEOUT,
    proxy: str | None = None,
    follow_redirects: bool = False,
) -> httpx.AsyncClient:
    """Create an httpx.AsyncClient with common settings.

    Args:
        timeout: Request timeout in seconds.
        proxy: Optional proxy URL (http://, socks5://, etc.).
        follow_redirects: Whether to follow HTTP redirects.

    Returns:
        Configured httpx.AsyncClient instance.
    """
    return httpx.AsyncClient(
        timeout=timeout,
        proxy=proxy,
        follow_redirects=follow_redirects,
    )
