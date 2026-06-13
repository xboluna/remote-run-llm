"""SSH connection management with opinionated defaults."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import paramiko

from remote_run.auth import build_connect_kwargs
from remote_run.errors import wrap_paramiko_error

DEFAULT_CONNECT_TIMEOUT = 30.0
DEFAULT_COMMAND_TIMEOUT = 300.0


def strict_host_keys_enabled() -> bool:
    """Return True when SSH_STRICT=1 enables known_hosts verification."""
    return os.environ.get("SSH_STRICT", "").strip() in {"1", "true", "yes", "on"}


def apply_host_key_policy(client: paramiko.SSHClient) -> None:
    """Apply strict or permissive host key policy."""
    if strict_host_keys_enabled():
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        return
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())


@contextmanager
def ssh_client(
    host: str,
    *,
    user: str | None = None,
    password: str | None = None,
    key: str | None = None,
    key_passphrase: str | None = None,
    port: int = 22,
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
) -> Iterator[paramiko.SSHClient]:
    """Open and always close an SSH client for the given host."""
    client = paramiko.SSHClient()
    apply_host_key_policy(client)
    connect_kwargs = build_connect_kwargs(
        user=user,
        password=password,
        key=key,
        key_passphrase=key_passphrase,
        port=port,
        connect_timeout=connect_timeout,
    )
    try:
        client.connect(hostname=host, **connect_kwargs)
    except Exception as exc:  # noqa: BLE001 - wrap all connect failures
        raise wrap_paramiko_error(exc, context=f"SSH connect to {host}") from exc
    try:
        yield client
    finally:
        client.close()


def exec_remote_command(
    client: paramiko.SSHClient,
    command: str,
    *,
    command_timeout: float = DEFAULT_COMMAND_TIMEOUT,
) -> tuple[str, str, int]:
    """Execute a command and return decoded stdout, stderr, and exit code."""
    stdin, stdout, stderr = client.exec_command(command, timeout=command_timeout)
    stdin.close()
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return out, err, exit_code


def transfer_file(
    client: paramiko.SSHClient,
    *,
    local_path: str,
    remote_path: str,
    upload: bool,
) -> None:
    """Upload or download a single file via SFTP."""
    with client.open_sftp() as sftp:
        if upload:
            sftp.put(local_path, remote_path)
        else:
            sftp.get(remote_path, local_path)


def connect_kwargs_for_testing(**overrides: Any) -> dict[str, Any]:
    """Expose connect kwargs builder for unit tests."""
    return build_connect_kwargs(
        user=overrides.get("user"),
        password=overrides.get("password"),
        key=overrides.get("key"),
        key_passphrase=overrides.get("key_passphrase"),
        port=overrides.get("port", 22),
        connect_timeout=overrides.get("connect_timeout", DEFAULT_CONNECT_TIMEOUT),
    )
