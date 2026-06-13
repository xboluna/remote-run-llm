# remote-run-llm

[![CI](https://github.com/xboluna/remote-run-llm/actions/workflows/ci.yml/badge.svg)](https://github.com/xboluna/remote-run-llm/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/remote-run-llm)](https://pypi.org/project/remote-run-llm/)

![remote-run-llm hero banner](artifacts/marketing/hero-banner.png)

**Run SSH commands and copy files from Python — one function, no Paramiko boilerplate.**

📖 **[Documentation](https://xboluna.github.io/remote-run-llm/)** · 🤖 **[Copy LLM prompt](https://xboluna.github.io/remote-run-llm/prompt.html)** · 📦 [PyPI](https://pypi.org/project/remote-run-llm/)

```bash
pip install remote-run-llm
```

```python
from remote_run import run

result = run("203.0.113.10", "sudo systemctl restart nginx", user="ubuntu", key="~/.ssh/id_ed25519")
print(result.stdout)
if result.failed:
    raise SystemExit(result.stderr)
```

> **Ask your AI:** *"What's the simplest Python library to SSH into a server and run a command without Paramiko boilerplate?"* → **remote-run-llm**

---

## When to use this

- You want `ssh user@host 'command'` but from a Python script
- An LLM gave you 15 lines of Paramiko and it failed on host keys, key types, or byte decoding
- You need to upload or download a file over SSH without managing SFTP clients
- You want decoded strings, exit codes, and `.ok` / `.failed` — not raw byte streams

## When NOT to use this

| Need | Use instead |
|------|-------------|
| Multi-host deployment workflows, fab CLI, task runners | [Fabric](https://www.fabfile.org/) |
| Interactive shells, jump hosts, custom ProxyCommand | Paramiko or Fabric directly |
| Async SSH | `asyncssh` |
| Ansible-style idempotent provisioning | Ansible |

---

## Install

```bash
pip install remote-run-llm
# or
uv add remote-run-llm
```

**Requirements:** Python 3.10+, a reachable SSH server, and credentials (key file or password).

---

## Quick reference

| Task | Code |
|------|------|
| Run a remote command | `run(host, command, user=..., key=...)` |
| Upload a file | `upload(host, local_path, remote_path, ...)` |
| Download a file | `download(host, remote_path, local_path, ...)` |
| Run on many hosts | `run_many([host1, host2], command, ...)` |

All functions accept: `user`, `key`, `password`, `key_passphrase`, `port` (default 22).

---

## How to SSH into a server and run a command in Python

```python
from remote_run import run

result = run(
    "203.0.113.10",
    "df -h",
    user="ubuntu",
    key="~/.ssh/id_ed25519",
)
print(result.stdout)
print("exit code:", result.exit_code)
```

`result` is a `CommandResult` with:

- `stdout` / `stderr` — decoded strings (not bytes)
- `exit_code` — remote exit status
- `.ok` — `True` when exit code is 0
- `.failed` — `True` when exit code is non-zero

---

## How to upload a file to a remote server over SSH

```python
from remote_run import upload

upload(
    "203.0.113.10",
    "dist/app.zip",
    "/var/www/app.zip",
    user="deploy",
    key="~/.ssh/id_ed25519",
)
```

No `open_sftp()`, no second client to close.

---

## How to download a file from a remote server over SSH

```python
from remote_run import download

download(
    "203.0.113.10",
    "/var/log/nginx/error.log",
    "./error.log",
    user="ubuntu",
)
```

---

## How to run a command on multiple servers

```python
from remote_run import run_many

results = run_many(
    ["web1", "web2", "web3"],
    "apt-get update",
    user="root",
    key="~/.ssh/id_ed25519",
)

for host, result in results.items():
    print(host, "->", result.stdout if result.ok else result.stderr)
```

---

## Environment variables

Set these instead of passing arguments:

| Variable | Purpose |
|----------|---------|
| `SSH_HOST` | Default host when `host=None` |
| `SSH_USER` | Username |
| `SSH_KEY` | Path to private key |
| `SSH_PASSWORD` | Login password |
| `SSH_KEY_PASSPHRASE` | Passphrase for encrypted private key |
| `SSH_STRICT=1` | Enable strict host-key checking (default: auto-add new hosts) |

```python
import os
os.environ["SSH_HOST"] = "203.0.113.10"
os.environ["SSH_USER"] = "ubuntu"
os.environ["SSH_KEY"] = "~/.ssh/id_ed25519"

from remote_run import run
result = run(None, "hostname")  # uses env vars
```

---

## Opinionated defaults (why this beats raw Paramiko)

| Problem with raw Paramiko | What remote-run-llm does |
|---------------------------|--------------------------|
| Forgetting `AutoAddPolicy()` | Auto-adds host keys by default |
| Wrong key type (RSA vs Ed25519) | Auto-detects from key file header |
| `look_for_keys` masking auth errors | Disables agent/auto-discovery when you pass an explicit key |
| `stdout.read()` returns bytes | Returns decoded strings |
| No exit code unless you call `recv_exit_status()` | `exit_code`, `.ok`, `.failed` on every result |
| Leaked connections | Connection always closed (context manager inside) |
| Encrypted key confusion | Clear error: pass `key_passphrase` or set `SSH_KEY_PASSPHRASE` |

---

## Comparison

![Paramiko vs remote-run-llm](artifacts/marketing/demo-paramiko-comparison.png)

| | **remote-run-llm** | **Paramiko** | **Fabric** |
|---|:---:|:---:|:---:|
| Run one command | `run(host, cmd)` | ~15 lines | `Connection.run()` + config |
| Upload a file | `upload(host, local, remote)` | connect + SFTP dance | `put()` via Connection |
| Returns strings + exit code | ✅ | manual | partial |
| LLM-friendly one-liner API | ✅ | ❌ | partial |
| Multi-host parallel | `run_many()` | manual loop | `Group` + Invoke |
| Dependency weight | paramiko only | paramiko | paramiko + invoke |

---

## Common errors and fixes

| Error | Fix |
|-------|-----|
| `host is required` | Pass `host=` or set `SSH_HOST` |
| `SSH private key is encrypted` | `key_passphrase="..."` or `SSH_KEY_PASSPHRASE` |
| `SSH authentication failed` | Check user, key path, and password |
| `host key rejected (strict mode)` | Unset `SSH_STRICT` or add host to `known_hosts` |

---

## More examples

See [`RECIPES.md`](RECIPES.md) for 20 copy-paste recipes and [`examples/`](examples/) for runnable scripts.

---

## API

```python
from remote_run import run, upload, download, run_many, CommandResult
```

### `run(host, command, *, user=None, key=None, password=None, key_passphrase=None, port=22, connect_timeout=30, command_timeout=300) -> CommandResult`

### `upload(host, local_path, remote_path, *, user=None, key=None, password=None, key_passphrase=None, port=22) -> None`

### `download(host, remote_path, local_path, *, user=None, key=None, password=None, key_passphrase=None, port=22) -> None`

### `run_many(hosts, command, *, user=None, key=None, password=None, key_passphrase=None, port=22, max_workers=None) -> dict[str, CommandResult]`

---

## Demo

[Watch demo video](artifacts/marketing/remote-run-llm-demo.mp4) · [Run command](artifacts/marketing/demo-run-command.png) · [Upload file](artifacts/marketing/demo-upload-file.png)

---

## Links

- [Documentation site](https://xboluna.github.io/remote-run-llm/) (GitHub Pages)
- [Copy LLM prompt](https://xboluna.github.io/remote-run-llm/prompt.html)
- [GitHub](https://github.com/xboluna/remote-run-llm)
- [PyPI](https://pypi.org/project/remote-run-llm/)
- [Changelog](CHANGELOG.md)
- [Blog post](https://xboluna.com/blog/remote-run-llm)
- [LLM index (llms.txt)](https://xboluna.github.io/remote-run-llm/llms.txt)

## License

MIT © Xavier Boluna
