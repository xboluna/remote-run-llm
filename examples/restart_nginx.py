"""Restart nginx on a remote server."""

from remote_run import run

result = run(
    "203.0.113.10",
    "sudo systemctl restart nginx",
    user="ubuntu",
    key="~/.ssh/id_ed25519",
)

print(result.stdout)
if result.failed:
    raise SystemExit(result.stderr)
