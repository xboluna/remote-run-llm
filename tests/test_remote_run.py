from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import paramiko
import pytest

from remote_run import CommandResult, download, run, run_many, upload
from remote_run.auth import (
    build_connect_kwargs,
    discover_default_key,
    load_private_key,
    resolve_host,
)
from remote_run.connection import apply_host_key_policy, strict_host_keys_enabled
from remote_run.errors import RemoteRunError, wrap_paramiko_error


def test_command_result_ok_and_failed() -> None:
    success = CommandResult(stdout="ok", stderr="", exit_code=0, host="h", command="c")
    failure = CommandResult(
        stdout="", stderr="nope", exit_code=1, host="h", command="c"
    )

    assert success.ok is True
    assert success.failed is False
    assert failure.ok is False
    assert failure.failed is True


def test_resolve_host_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SSH_HOST", "example.com")
    assert resolve_host(None) == "example.com"
    assert resolve_host("override.com") == "override.com"


def test_resolve_host_missing_raises() -> None:
    with pytest.raises(ValueError, match="host is required"):
        resolve_host(None)


def test_strict_host_keys_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SSH_STRICT", raising=False)
    assert strict_host_keys_enabled() is False
    monkeypatch.setenv("SSH_STRICT", "1")
    assert strict_host_keys_enabled() is True


def test_apply_host_key_policy_auto_add(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SSH_STRICT", raising=False)
    client = MagicMock(spec=paramiko.SSHClient)
    apply_host_key_policy(client)
    client.set_missing_host_key_policy.assert_called_once()
    assert isinstance(
        client.set_missing_host_key_policy.call_args.args[0],
        paramiko.AutoAddPolicy,
    )


def test_apply_host_key_policy_strict(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SSH_STRICT", "1")
    client = MagicMock(spec=paramiko.SSHClient)
    apply_host_key_policy(client)
    client.load_system_host_keys.assert_called_once()
    assert isinstance(
        client.set_missing_host_key_policy.call_args.args[0],
        paramiko.RejectPolicy,
    )


def test_build_connect_kwargs_explicit_key_disables_agent(tmp_path: Path) -> None:
    key_path = tmp_path / "id_ed25519"
    key_path.write_text("not-a-real-key")

    with patch("remote_run.auth.load_private_key", return_value=MagicMock()):
        kwargs = build_connect_kwargs(
            user="ubuntu",
            password=None,
            key=str(key_path),
            key_passphrase=None,
            port=22,
            connect_timeout=30.0,
        )

    assert kwargs["look_for_keys"] is False
    assert kwargs["allow_agent"] is False
    assert "pkey" in kwargs


def test_wrap_paramiko_password_required() -> None:
    err = wrap_paramiko_error(
        paramiko.ssh_exception.PasswordRequiredException("encrypted"),
        context="connect",
    )
    assert isinstance(err, RemoteRunError)
    assert "SSH_KEY_PASSPHRASE" in str(err)


def test_run_returns_command_result() -> None:
    mock_client = MagicMock(spec=paramiko.SSHClient)
    mock_stdout = MagicMock()
    mock_stderr = MagicMock()
    mock_stdin = MagicMock()
    mock_stdout.channel.recv_exit_status.return_value = 0
    mock_stdout.read.return_value = b"hello\n"
    mock_stderr.read.return_value = b""
    mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

    with patch("remote_run.run.ssh_client") as ssh_ctx:
        ssh_ctx.return_value.__enter__.return_value = mock_client
        result = run("203.0.113.10", "echo hello", user="ubuntu")

    assert result.stdout == "hello\n"
    assert result.stderr == ""
    assert result.exit_code == 0
    assert result.ok is True
    assert result.host == "203.0.113.10"
    assert result.command == "echo hello"


def test_upload_calls_sftp_put() -> None:
    mock_client = MagicMock(spec=paramiko.SSHClient)
    mock_sftp = MagicMock()
    mock_client.open_sftp.return_value.__enter__.return_value = mock_sftp

    with patch("remote_run.files.ssh_client") as ssh_ctx:
        ssh_ctx.return_value.__enter__.return_value = mock_client
        upload("203.0.113.10", "local.txt", "/remote/local.txt", user="deploy")

    mock_sftp.put.assert_called_once_with("local.txt", "/remote/local.txt")


def test_download_calls_sftp_get() -> None:
    mock_client = MagicMock(spec=paramiko.SSHClient)
    mock_sftp = MagicMock()
    mock_client.open_sftp.return_value.__enter__.return_value = mock_sftp

    with patch("remote_run.files.ssh_client") as ssh_ctx:
        ssh_ctx.return_value.__enter__.return_value = mock_client
        download("203.0.113.10", "/remote/log.txt", "./log.txt")

    mock_sftp.get.assert_called_once_with("/remote/log.txt", "./log.txt")


def test_run_many_returns_per_host_results() -> None:
    def fake_run(host: str, command: str, **_: object) -> CommandResult:
        return CommandResult(
            stdout=f"out-{host}",
            stderr="",
            exit_code=0,
            host=host,
            command=command,
        )

    with patch("remote_run.batch.run", side_effect=fake_run):
        results = run_many(["web1", "web2"], "hostname", user="root")

    assert set(results) == {"web1", "web2"}
    assert results["web1"].stdout == "out-web1"


def test_run_many_empty_hosts() -> None:
    assert run_many([], "true") == {}


def test_load_private_key_ed25519(tmp_path: Path) -> None:
    # Generate a minimal ed25519 key for testing using paramiko
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519

    private_key = ed25519.Ed25519PrivateKey.generate()
    key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    key_path = tmp_path / "id_ed25519"
    key_path.write_bytes(key_bytes)

    loaded = load_private_key(key_path, None)
    assert isinstance(loaded, paramiko.Ed25519Key)


def test_discover_default_key_returns_none_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "remote_run.auth.DEFAULT_KEY_CANDIDATES",
        ("/nonexistent/id_ed25519", "/nonexistent/id_rsa"),
    )
    assert discover_default_key() is None
