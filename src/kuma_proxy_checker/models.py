from enum import StrEnum


class Status(StrEnum):
    UP = "up"
    DOWN = "down"
    OK = "OK"
    FAILED = "FAILED"
    ERROR = "ERROR"


class ProxyScheme(StrEnum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"
    SOCKS5H = "socks5h"
