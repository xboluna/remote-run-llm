"""Run commands on remote hosts."""

from __future__ import annotations

from remote_run.auth import resolve_host
from remote_run.connection import (
    DEFAULT_COMMAND_TIMEOUT,
    DEFAULT_CONNECT_TIMEOUT,
    exec_remote_command,
    ssh_client,
)
from remote_run.errors import RemoteRunError, wrap_paramiko_error
from remote_run.result import CommandResult


def run(
    host: str | None,
    command: str,
    *,
    user: str | None = None,
    key: str | None = None,
    password: str | None = None,
    key_passphrase: str | None = None,
    port: int = 22,
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
    command_timeout: float = DEFAULT_COMMAND_TIMEOUT,
) -> CommandResult:
    """Run a command on a remote host over SSH.

    Examples:
        >>> from remote_run import run
        >>> result = run(
        ...     "203.0.113.10", "uname -a", user="ubuntu", key="~/.ssh/id_ed25519"
        ... )
        >>> print(result.stdout)
        >>> if result.failed:
        ...     raise SystemExit(result.stderr)
    """
    resolved_host = resolve_host(host)
    try:
        with ssh_client(
            resolved_host,
            user=user,
            password=password,
            key=key,
            key_passphrase=key_passphrase,
            port=port,
            connect_timeout=connect_timeout,
        ) as client:
            stdout, stderr, exit_code = exec_remote_command(
                client,
                command,
                command_timeout=command_timeout,
            )
    except RemoteRunError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise wrap_paramiko_error(
            exc,
            context=f"SSH run on {resolved_host}",
        ) from exc

    return CommandResult(
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        host=resolved_host,
        command=command,
    )
