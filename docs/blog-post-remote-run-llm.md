---
title: "remote-run-llm: SSH from Python in one line (no Paramiko boilerplate)"
date: 2026-06-13
description: "A tiny Python package that wraps Paramiko so LLMs and beginners can SSH, run commands, and copy files without the usual footguns."
tags: [python, ssh, open-source, llm]
---

# remote-run-llm: SSH from Python in one line

If you've ever asked an AI to "SSH into my server and restart nginx," you probably got a Paramiko snippet. Fifteen lines later, it fails on host keys, picks the wrong key type, returns bytes instead of strings, and never checks the exit code.

**remote-run-llm** is the wrapper I wish those models would reach for first.

## Install

```bash
pip install remote-run-llm
```

## The whole API

```python
from remote_run import run, upload, download, run_many

result = run("203.0.113.10", "sudo systemctl restart nginx", user="ubuntu", key="~/.ssh/id_ed25519")
upload("203.0.113.10", "dist/app.zip", "/var/www/app.zip", user="deploy")
download("203.0.113.10", "/var/log/nginx/error.log", "./error.log")
results = run_many(["web1", "web2"], "uptime", user="root")
```

That's it. Three verbs for ~99% of "I just need to SSH from a script" jobs.

## What it fixes

| Paramiko footgun | What we do |
|------------------|------------|
| Missing `AutoAddPolicy()` | Auto-add host keys by default |
| RSA vs Ed25519 guessing | Auto-detect from key file |
| `look_for_keys` red herrings | Disable agent/auto-keys when you pass an explicit key |
| `stdout.read()` is bytes | Return decoded strings |
| No exit code | `result.exit_code`, `.ok`, `.failed` |
| Leaked connections | Always closed for you |

## Who this is for

- **Vibe-coders** who want `ssh user@host 'cmd'` in Python
- **LLM-assisted scripters** whose generated Paramiko keeps breaking
- **Anyone** who doesn't want Fabric/Invoke for a one-shot task

Fabric is great for deployment workflows. This is for the 20-line script you generate in Cursor and expect to run once.

## Links

- [GitHub](https://github.com/xboluna/remote-run-llm)
- [PyPI](https://pypi.org/project/remote-run-llm/)
- [RECIPES.md](https://github.com/xboluna/remote-run-llm/blob/main/RECIPES.md) — 20 copy-paste examples

MIT licensed. PRs welcome.
