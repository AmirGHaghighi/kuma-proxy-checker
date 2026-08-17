# kuma-proxy-checker

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Release](https://img.shields.io/github/v/release/AmirGHaghighi/kuma-proxy-checker)](https://github.com/AmirGHaghighi/kuma-proxy-checker/releases)

Async proxy health checker that tests a list of proxies with real HTTP requests and reports
per-proxy **up/down** status to [Uptime Kuma](https://github.com/louislam/uptime-kuma)-style
push URLs.

## Features

- Tests each proxy by making an HTTP request through it against a configurable `test_url`
- Validates the response against an expected HTTP status code
- Configurable per-attempt timeout, retry count, and retry backoff delay
- Pushes `up`/`down` status to Uptime Kuma push endpoints (compatible with the `push` type monitor)
- Runs continuously on an interval, or as a single check cycle with `--once`
- Supports `http`, `https`, `socks4`, `socks5`, and `socks5h` proxies
- Async (`asyncio` + `httpx`): all targets are checked concurrently
- Clean exits on `SIGINT`/`SIGTERM`
- Ships as a single self-contained executable via Nuitka builds

## Requirements

- Python 3.11 or newer
- For the prebuilt binaries: nothing — they are self-contained

## Installation

### From source

```bash
git clone https://github.com/AmirGHaghighi/kuma-proxy-checker.git
cd kuma-proxy-checker

python -m venv .venv
# Unix: source .venv/bin/activate   |   Windows: .venv\Scripts\Activate.ps1
pip install .
```

This installs the `kuma-proxy-checker` command. It can also be run as a module:

```bash
python -m kuma_proxy_checker -c config.json
```

### Development install

```bash
pip install -e ".[dev]"
```

### Prebuilt binaries

Self-contained executables for Linux and Windows are published on the
[Releases page](https://github.com/AmirGHaghighi/kuma-proxy-checker/releases).
No Python install is required.

## Quick start

1. Copy the example config and edit it:

```bash
cp config.example.json config.json
```

2. Point the `test_url` at a reliable endpoint that returns a predictable status code
   (e.g. `https://www.gstatic.com/generate_204` returning `204`).

3. For each target, set the proxy URL and the Uptime Kuma push URL
   (from a **Push** type monitor in Uptime Kuma: `https://your-kuma/api/push/<token>`).

4. Run it on a 5-minute loop:

```bash
kuma-proxy-checker -c config.json
```

Or once:

```bash
kuma-proxy-checker -c config.json --once
```

## CLI

| Flag                    | Description                                        |
| ----------------------- | -------------------------------------------------- |
| `-c, --config`          | Path to the config JSON file (required)            |
| `--once`                | Run a single check cycle, then exit                |
| `-v, --verbose`         | Enable debug logging                               |
| `--version`             | Print the version and exit                         |

## Configuration

All fields except `remark` are required unless a default is noted.

| Field                   | Type   | Default | Description                                          |
| ----------------------- | ------ | ------- | ---------------------------------------------------- |
| `test_url`              | string | —       | URL requested through each proxy                     |
| `expected_status`       | int    | —       | HTTP status code that counts as healthy (100-599)    |
| `retries`               | int    | `3`     | Attempts per proxy before reporting failure (>=1)    |
| `timeout_seconds`       | float  | `10.0`  | Per-request timeout                              |
| `retry_delay_seconds`   | float  | `1.0`   | Sleep between retry attempts (>=0)                   |
| `interval_minutes`      | int    | `5`     | Minutes between cycles (`0` disables looping)      |
| `targets`               | array  | —       | At least one target object (see below)               |

Each target:

| Field      | Type    | Description                                        |
| ---------- | ------- | -------------------------------------------------- |
| `proxy`    | string  | Proxy URL, e.g. `socks5://user:pass@host:1080`    |
| `push_url` | string  | Uptime Kuma push URL to report status to           |
| `remark`   | string  | Optional human-readable identifier for logs/msgs   |

Allowed proxy schemes: `http`, `https`, `socks4`, `socks5`, `socks5h`.
Unsupported schemes fail config validation at startup.

```json
{
  "test_url": "https://www.gstatic.com/generate_204",
  "expected_status": 204,
  "retries": 3,
  "timeout_seconds": 10.0,
  "retry_delay_seconds": 2.0,
  "interval_minutes": 5,
  "targets": [
    {
      "proxy": "socks5://192.168.10.1:10808",
      "push_url": "https://kuma.example.com/api/push/abc123",
      "remark": "datacenter-1"
    }
  ]
}
```

## How it works

1. Config is loaded and validated with Pydantic (schemes, ranges, target count).
2. Every cycle, all targets are checked concurrently with `asyncio.gather`.
3. For each target, the proxy is tested against `test_url`; a mismatch with
   `expected_status` or any connection error counts as a failure and is retried
   up to `retries` times with `retry_delay_seconds` between attempts.
4. The result is pushed to the target's `push_url` via a GET with query params:

   - `status` — `up` or `down`
   - `msg` — human-readable message, e.g. `OK : datacenter-1 : OK (120ms)`
   - `ping` — measured latency in milliseconds (present when the proxy is up)

5. The loop sleeps `interval_minutes` and repeats, unless `--once` was passed,
   `interval_minutes` is `0`, or the process received a shutdown signal.

## Building from source (Nuitka)

```bash
pip install nuitka
python -m nuitka \
  --onefile --standalone \
  --output-filename=kuma-proxy-checker \
  src/kuma_proxy_checker/cli.py
```

On Windows a C toolchain is required (MinGW64 recommended). The exact flags used for
release builds are defined in `.github/workflows/release.yaml`, and binaries are
published automatically when a `v*` tag is pushed.

## Development

```bash
pip install -e ".[dev]"

pytest        # run tests
ruff check .  # lint
```

## Contributing

Contributions are welcome. Please open an issue to discuss changes before opening a
pull request, and keep the existing code style (linted with Ruff, tests green).

## License

[GPL-3.0](LICENSE) © AmirGHaghighi