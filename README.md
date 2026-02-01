# kuma-proxy-checker ✅

**Proxy health checker that tests proxies and pushes per-proxy status to Uptime Kuma-style push endpoints.**

---

## 🔧 Features

- Test a list of proxies by making HTTP requests through each proxy
- Retry failed attempts with configurable retries and timeouts
- Send status updates (up/down) to Uptime Kuma-style push URLs
- Run continuously on an interval or run a single check cycle with `--once`

---

## ⚙️ Requirements

- **Python 3.8+**
- Dependencies in `requirements.txt` (install with pip)

---

## 🚀 Installation

1. Clone the repository:

```bash
git clone https://github.com/AmirGHaghighi/kuma-proxy-checker.git
cd kuma-proxy-checker
```

2. Create and activate a virtual environment (recommended):

- On macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

- On Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🧩 Configuration

Copy `config-example.json` to `config.json` and edit it to suit your needs.

A working example (see `config-example.json`):

```json
{
  "test_url": "https://example.com/health204",
  "expected_status": 204,
  "retries": 3,
  "timeout_seconds": 10,
  "retry_delay_seconds": 2,
  "interval_minutes": 5,
  "targets": [
    {
      "proxy": "socks5://192.168.10.1:10808",
      "push_url": "https://kuma/api/push/AAA"
    }
  ]
}
```

Required configuration fields:

- `test_url` (string): URL to request through each proxy (health endpoint is recommended)
- `expected_status` (int): HTTP status code expected for a successful check (e.g., 204)
- `retries` (int): Number of attempts per check before reporting failure
- `timeout_seconds` (float): Request timeout for each attempt
- `retry_delay_seconds` (float): Delay between retry attempts (seconds)
- `interval_minutes` (int): Minutes between automatic check cycles (<= 0 to disable looping)
- `targets` (array): List of target objects, each with:
  - `proxy` (string): Proxy URL (required)
  - `push_url` (string): Uptime Kuma push URL to report status to (required)
  - `remark` (string): Optional human remark/identifier

Allowed proxy URL schemes: **http, https, socks4, socks5, socks5h**. The tool will validate the scheme and raise an error for unsupported ones.

---

## 🧭 CLI Usage

Run the checker with the required config file:

```bash
python main.py -c config.json
```

Run a single check cycle (do not loop):

```bash
python main.py -c config.json --once
```

Arguments:

- `-c, --config` **(required)** Path to the config JSON file
- `--once` Run one check cycle and exit instead of looping on an interval

---

## 📡 How notifications are sent

- The app sends a GET request to each `push_url` with query parameters:
  - `status` — `up` or `down`
  - `msg` — human-readable message (e.g., `OK : <remark> : OK (950 ms)`)
  - `ping` — latency in ms (if available)

This is compatible with Uptime Kuma's push API endpoints.

---

## 🧰 Logs & Troubleshooting

- The app logs events to stdout (INFO level by default). Typical messages include `OK`, `FAILED`, and `ERROR` with proxy identifiers and context.
- If a push fails, the app logs the failure but continues to check other targets.

> Tip: Use a minimal `test_url` that reliably returns a predictable status code (e.g., `/generate_204`) to reduce false negatives.

---

## 🏃 Running in production

- On Linux, consider running with `systemd` or a process supervisor (supervisord, Docker, etc.)
- On Windows, use Task Scheduler or a service wrapper (such as NSSM) to run the script on startup

---

## 🤝 Contributing

Contributions are welcome — open issues and pull requests for bug fixes or features.

---

## 📄 License

This repository is licensed under the **GNU General Public License v3.0 (GPL-3.0)

---

If you'd like I can add example systemd unit, Dockerfile, or CI workflow next. ✨
