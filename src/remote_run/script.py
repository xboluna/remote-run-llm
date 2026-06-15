"""Upload a local script and run it on a remote host in one SSH session."""

from __future__ import annotations

import shlex
import uuid
from pathlib import Path

from remote_run import connection
from remote_run.auth import resolve_host
from remote_run.errors import RemoteRunError, wrap_paramiko_error
from remote_run.result import CommandResult

DEFAULT_REMOTE_DIR = "/tmp/remote-run-llm"

_INTERPRETER_BY_SUFFIX = {
    ".py": "python3",
    ".sh": "bash",
    ".bash": "bash",
    ".rb": "ruby",
    ".pl": "perl",
    ".js": "node",
}


def _default_interpreter(local_path: Path) -> str | None:
    return _INTERPRETER_BY_SUFFIX.get(local_path.suffix.lower())


def _read_shebang(local_path: Path) -> str | None:
    with local_path.open(encoding="utf-8", errors="replace") as handle:
        first_line = handle.readline().strip()
    if first_line.startswith("#!"):
        return first_line[2:].strip()
    return None


def _remote_script_path(local_path: Path, remote_dir: str) -> str:
    unique = uuid.uuid4().hex[:8]
    return f"{remote_dir}/{local_path.stem}-{unique}{local_path.suffix}"


def _build_run_command(
    remote_path: str,
    args: tuple[str, ...],
    *,
    interpreter: str | None,
    local_path: Path,
) -> str:
    quoted_remote = shlex.quote(remote_path)
    quoted_args = " ".join(shlex.quote(arg) for arg in args)

    resolved_interpreter = interpreter
    if resolved_interpreter is None:
        resolved_interpreter = _default_interpreter(local_path)

    if resolved_interpreter is None:
        shebang = _read_shebang(local_path)
        if shebang:
            command = f"chmod +x {quoted_remote} && {shebang} {quoted_remote}"
            if quoted_args:
                command += f" {quoted_args}"
            return command
        raise ValueError(
            f"Cannot determine how to run {local_path!s}; "
            "pass interpreter= (e.g. interpreter='python3')."
        )

    command = f"{resolved_interpreter} {quoted_remote}"
    if quoted_args:
        command += f" {quoted_args}"
    return command


def run_script(
    host: str | None,
    local_path: str,
    *args: str,
    user: str | None = None,
    key: str | None = None,
    password: str | None = None,
    key_passphrase: str | None = None,
    port: int = 22,
    connect_timeout: float = connection.DEFAULT_CONNECT_TIMEOUT,
    command_timeout: float = connection.DEFAULT_COMMAND_TIMEOUT,
    interpreter: str | None = None,
    remote_dir: str = DEFAULT_REMOTE_DIR,
    cleanup: bool = True,
) -> CommandResult:
    """Upload a local script and execute it on a remote host.

    Edits stay on your machine — the file is copied over SFTP, run once, and
    removed by default. Uses a single SSH connection for upload and execution.

    Examples:
        >>> from remote_run import run_script
        >>> result = run_script(
        ...     "192.168.1.101",
        ...     "hello.py",
        ...     user="ubuntu",
        ...     key="~/.ssh/id_ed25519",
        ... )
        >>> result = run_script("vm.local", "deploy.sh", "--dry-run", user="deploy")
    """
    local_file = Path(local_path).expanduser()
    if not local_file.is_file():
        raise FileNotFoundError(f"Local script not found: {local_file}")

    resolved_host = resolve_host(host)
    remote_path = _remote_script_path(local_file, remote_dir)
    run_command = _build_run_command(
        remote_path,
        args,
        interpreter=interpreter,
        local_path=local_file,
    )
    if cleanup:
        quoted_remote = shlex.quote(remote_path)
        run_command = f"{run_command}; ec=$?; rm -f {quoted_remote}; exit $ec"

    try:
        with connection.ssh_client(
            resolved_host,
            user=user,
            password=password,
            key=key,
            key_passphrase=key_passphrase,
            port=port,
            connect_timeout=connect_timeout,
        ) as client:
            quoted_remote_dir = shlex.quote(remote_dir)
            connection.exec_remote_command(
                client,
                f"mkdir -p {quoted_remote_dir}",
                command_timeout=command_timeout,
            )
            connection.transfer_file(
                client,
                local_path=str(local_file),
                remote_path=remote_path,
                upload=True,
            )
            stdout, stderr, exit_code = connection.exec_remote_command(
                client,
                run_command,
                command_timeout=command_timeout,
            )
    except RemoteRunError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise wrap_paramiko_error(
            exc,
            context=f"SSH run_script on {resolved_host}",
        ) from exc

    return CommandResult(
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        host=resolved_host,
        command=run_command,
    )
