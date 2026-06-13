"""Human-readable error messages for common Paramiko failures."""

from __future__ import annotations

import paramiko


class RemoteRunError(Exception):
    """Base error for remote-run-llm with actionable guidance."""


def wrap_paramiko_error(exc: BaseException, *, context: str) -> RemoteRunError:
    """Convert Paramiko exceptions into messages LLMs and humans can act on."""
    if isinstance(exc, paramiko.ssh_exception.PasswordRequiredException):
        return RemoteRunError(
            f"{context}: SSH private key is encrypted. "
            "Pass key_passphrase='...' or set SSH_KEY_PASSPHRASE."
        )
    if isinstance(exc, paramiko.ssh_exception.AuthenticationException):
        return RemoteRunError(
            f"{context}: SSH authentication failed. "
            "Check user/password/key path. When passing an explicit key, "
            "this package disables agent and ~/.ssh auto-discovery to avoid "
            "misleading errors — verify the key file and passphrase."
        )
    if isinstance(
        exc, paramiko.ssh_exception.SSHException
    ) and "not found in known_hosts" in str(exc):
        return RemoteRunError(
            f"{context}: host key rejected (strict mode). "
            "Unset SSH_STRICT or add the host to ~/.ssh/known_hosts."
        )
    if isinstance(exc, paramiko.ssh_exception.NoValidConnectionsError):
        return RemoteRunError(
            f"{context}: could not connect. Check host, port, and firewall rules."
        )
    if isinstance(exc, FileNotFoundError):
        return RemoteRunError(f"{context}: file not found — {exc}")
    if isinstance(exc, OSError) and exc.errno == 2:
        return RemoteRunError(f"{context}: file not found — {exc}")
    return RemoteRunError(f"{context}: {exc}")
