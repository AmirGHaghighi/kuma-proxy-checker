# kuma-proxy-checker

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Release](https://img.shields.io/github/v/release/AmirGHaghighi/kuma-proxy-checker)](https://github.com/AmirGHaghighi/kuma-proxy-checker/releases)

Async proxy health checker that tests a list of proxies with real HTTP requests and reports
per-proxy **up/down** status to [Uptime Kuma](https://github.com/louislam/uptime-kuma)-style
push URLs.

## Features

- Tests each proxy by making an HTTP request through it against a configurable `default_test_url` (overridable per target)
- Validates the response against an expected HTTP status code
- Configurable per-attempt timeout, retry count, and retry backoff delay
- Pushes `up`/`down` status to Uptime Kuma push endpoints (compatible with the `push` type monitor)
- Runs continuously on an interval, or as a single check cycle with `--once`
- Supports `http`, `https`, `socks4`, `socks5`, and `socks5h` proxies
- Async (`asyncio` + `httpx`): all proxy targets are checked concurrently
- Clean exits on `SIGINT`/`SIGTERM`
- Ships as a single self-contained executable via Nuitka builds

## Requirements

- Python 3.11 or newer
- For the prebuilt binaries: nothing — they are self-contained

## Installation

### Quick install (Linux)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/AmirGHaghighi/kuma-proxy-checker/main/install.sh)
```

This downloads the latest binary to `~/.local/bin` and sets up a starter `config.json`.
You can pass a custom directory as an argument:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/AmirGHaghighi/kuma-proxy-checker/main/install.sh) /opt/kuma-proxy-checker
```

### Prebuilt binaries

Self-contained executables for Linux and Windows are available on the
[Releases page](https://github.com/AmirGHaghighi/kuma-proxy-checker/releases).
No Python install is required.

### Docker

Multi-arch images (`linux/amd64`, `linux/arm64`) are published to GitHub Container
Registry on every release tag:

```bash
docker run -d --name kuma-proxy-checker \
  --restart unless-stopped \
  -v "$PWD/config.json:/etc/kuma-proxy-checker/config.json" \
  ghcr.io/amirghaghighi/kuma-proxy-checker:latest
```

- The config must be mounted at `/etc/kuma-proxy-checker/config.json` (the container's
  default `-c` path); `config.example.json` is available inside the image at
  `/app/config.example.json`.
- The container runs as an unprivileged user. The optional health server
   (see `health_check_server` in the config) listens on port `8080` when enabled; use it for
  Docker/orchestrator liveness probes (there is no baked-in `HEALTHCHECK`).

Or with Docker Compose (a ready-made `compose.yaml` is in the repo):

```bash
docker compose up -d
```

This mounts `./config.json` into the container and publishes the health server port
(`8080`) when enabled.

**Host network mode** (Linux only; e.g. to reach proxies on `127.0.0.1:<port>`
running on the host, and to expose the health server without port mapping):

```bash
docker compose -f compose.yaml -f compose.host.yaml up -d
```

The `compose.host.yaml` override uses `network_mode: host`, so the health server
binds directly on the host interface/port from your config.

## Quick start

1. Copy the example config and edit it:

```bash
cp config.example.json config.json
```

2. Point `default_test_url` at a reliable endpoint that returns a predictable status code
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
| `default_test_url`     | string | —       | Default URL requested through each proxy (used when target has no `test_url`) |
| `expected_status`       | int    | —       | HTTP status code that counts as healthy (100-599)    |
| `retries`               | int    | `3`     | Attempts per proxy before reporting failure (>=1)    |
| `timeout_seconds`       | float  | `10.0`  | Per-request timeout                              |
| `retry_delay_seconds`   | float  | `1.0`   | Sleep between retry attempts (>=0)                   |
| `interval_minutes`      | int    | `5`     | Minutes between cycles (`0` disables looping)      |
| `proxy_targets`         | array  | —       | List of proxy target objects (see below)              |

Each target:

| Field      | Type    | Description                                        |
| ---------- | ------- | -------------------------------------------------- |
| `proxy`    | string  | Proxy URL, e.g. `socks5://user:pass@host:1080`    |
| `push_url` | string  | Uptime Kuma push URL to report status to           |
| `remark`   | string  | Optional human-readable identifier for logs/msgs   |
| `test_url` | string  | Optional per-target override for `default_test_url` |

Allowed proxy schemes: `http`, `https`, `socks4`, `socks5`, `socks5h`.
Unsupported schemes fail config validation at startup.

```json
{
  "default_test_url": "https://www.gstatic.com/generate_204",
  "expected_status": 204,
  "retries": 3,
  "timeout_seconds": 10.0,
  "retry_delay_seconds": 2.0,
  "interval_minutes": 5,
  "proxy_targets": [
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
2. Every cycle, all proxy targets are checked concurrently with `asyncio.gather`.
3. For each target, the proxy is tested against its `test_url` (falling back to
   `default_test_url` when not set); a mismatch with
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
git clone https://github.com/AmirGHaghighi/kuma-proxy-checker.git
cd kuma-proxy-checker

python -m venv .venv
# Unix: source .venv/bin/activate   |   Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

This installs the `kuma-proxy-checker` command in editable mode. It can also be run as a module:

```bash
python -m kuma_proxy_checker -c config.json
```

Run tests and lint:

```bash
pytest        # run tests
ruff check .  # lint
```

## Contributing

Contributions are welcome. Please open an issue to discuss changes before opening a
pull request, and keep the existing code style (linted with Ruff, tests green).

## License

[GPL-3.0](LICENSE) © AmirGHaghighi