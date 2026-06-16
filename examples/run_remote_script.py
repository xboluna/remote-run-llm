"""Run a local Python script on a remote VM — edit locally, execute remotely."""

from remote_run import run_script

result = run_script(
    "192.168.1.101",
    "hello.py",
    user="ubuntu",
    key="~/.ssh/id_ed25519",
)

print(result.stdout)
if result.failed:
    raise SystemExit(result.stderr)
