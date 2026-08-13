# kuma-proxy-checker

Proxy health checker: tests proxies via HTTP requests and pushes per-proxy up/down status to Uptime Kuma-style push URLs. GPL-3.0. GitHub: AmirGHaghighi/kuma-proxy-checker.

## Architecture

`src/kuma_proxy_checker/` package (src-layout, setuptools). Root `main.py` is the legacy single-file version; the packaged entry point is `src/kuma_proxy_checker/cli.py`. Modules:

- `cli.py` — argparse entry (`prog="proxy-monitor"`). Flags: `-c/--config` (required), `--once`, `-v/--verbose`, `--version`. `main()` → `asyncio.run(run_app(...))`.
- `app.py` — `ProxyMonitorApp` with constructor DI (`notifier`/`tester` injectable for tests). Handles SIGINT/SIGTERM via `asyncio` signal handlers + `_shutdown` Event. `run_cycle()` fans out with `asyncio.gather`; loop sleeps `interval_minutes`, exits on `--once`, `interval_minutes<=0`, or shutdown.
- `config.py` — Pydantic v2 models: `AppConfig`, `ProxyTarget`. Proxy scheme validated via `field_validator` + `PydanticCustomError`; `from_file()` uses `model_validate_json`.
- `models.py` — `Status` (`up/down/OK/FAILED/ERROR`) and `ProxyScheme` (`http/https/socks4/socks5/socks5h`) StrEnums.
- `tester.py` — `ProxyTester`: `httpx.AsyncClient(proxy=..., timeout=..., follow_redirects=True)` against `test_url`; returns `(ok, ping_ms, err_msg)`. `test_with_retries()` retries with `retry_delay_seconds` sleep.
- `notifier.py` — `NotifierProtocol` (Protoivial) + `UptimeKumaNotifier`: GET to push_url with params `status`, `msg`, `ping` (empty string when None).
- `logging_utils.py` — `setup_logging(verbose)`, `fmt_log(Status, identifier, message, ping)`, `get_identifier(target)` (remark or proxy URL).
- `__init__.py` — re-exports; `__version__` from `importlib.metadata`.

## Config JSON

Fields: `test_url`, `expected_status` (100-599), `retries` (>=1), `timeout_seconds` (>0), `retry_delay_seconds` (>=0), `interval_minutes` (>=0, 0 disables loop), `targets` (>=1 of `{proxy, push_url, remark?}`). Allowed proxy schemes: http, https, socks4, socks5, socks5h. `config.json` is gitignored; `config.example.json` is shipped into the binary.

## Dependencies (Python 3.11+)

`pyproject.toml` deps: `httpx`, `pydantic`. `requirements.txt` pins `httpx==0.28.1`, `socksio==1.0.0` (socksio provides SOCKS support for httpx). Build-time includes also pull `httpcore`, `anyio`, `sniffio`, `certifi`, `idna`, `pydantic_core`, `typing_extensions`.

## Testing & lint

- `pytest` with `pytest-asyncio` (`asyncio_mode = "auto"`, no `@pytest.mark.asyncio` needed). Shared `sample_config` fixture in `tests/conftest.py`. Run: `pytest`.
- Ruff config in `pyproject.toml`: quote-style double, line-length 100, select E,F,I,UP,W, ignore E501. Run: `ruff check .`

## Build / Release

- Binary built with Nuitka `--onefile --standalone` from `[tool.nuitka]` in pyproject + `.github/workflows/release.yaml` (matrix ubuntu + windows, Python 3.11). Windows uses MinGW via `choco install mingw --version=15.2.0`. No `--zig` flag in CI. Release auto-created on `v*` tag push, verifies `--version`/`--help`, ships SHA256 files.
- Include-data-file ships `config.example.json` into the binary.

### Known pitfall: `--zig` fails locally

Local machine's global pip index is a Nexus proxy `http://localhost:8081/repository/pypi-proxy/simple` that does NOT carry `ziglang` (and times out reaching upstream). Nuitka `--zig` auto-installs Zig via pip → `No matching distribution found for ziglang` → FATAL. Zig not installed system-wide (`zig: command not found`). Workarounds: drop `--zig` (MinGW64/MSVC in PATH), point `--zig=<path>\zig.exe` at a manual install, or `PIP_INDEX_URL=https://pypi.org/simple` for the bootstrap.