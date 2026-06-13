"""SSH authentication helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import paramiko

DEFAULT_KEY_CANDIDATES = (
    "~/.ssh/id_ed25519",
    "~/.ssh/id_rsa",
)


def resolve_host(host: str | None) -> str:
    """Resolve host from argument or SSH_HOST environment variable."""
    resolved = host or os.environ.get("SSH_HOST")
    if not resolved:
        raise ValueError("host is required (pass host= or set SSH_HOST)")
    return resolved


def resolve_user(user: str | None) -> str | None:
    """Resolve username from argument or SSH_USER environment variable."""
    return user or os.environ.get("SSH_USER")


def resolve_password(password: str | None) -> str | None:
    """Resolve login password from argument or SSH_PASSWORD."""
    return password or os.environ.get("SSH_PASSWORD")


def resolve_key_passphrase(key_passphrase: str | None) -> str | None:
    """Resolve key passphrase from argument or SSH_KEY_PASSPHRASE."""
    return key_passphrase or os.environ.get("SSH_KEY_PASSPHRASE")


def resolve_key_path(key: str | None) -> Path | None:
    """Resolve explicit key path from argument or SSH_KEY."""
    key_value = key or os.environ.get("SSH_KEY")
    if not key_value:
        return None
    return Path(key_value).expanduser()


def discover_default_key() -> Path | None:
    """Return the first existing default private key path."""
    for candidate in DEFAULT_KEY_CANDIDATES:
        path = Path(candidate).expanduser()
        if path.is_file():
            return path
    return None


def load_private_key(path: Path, passphrase: str | None) -> paramiko.PKey:
    """Load a private key, auto-detecting Ed25519, RSA, or ECDSA."""
    key_loaders: list[type[paramiko.PKey]] = [
        paramiko.Ed25519Key,
        paramiko.RSAKey,
        paramiko.ECDSAKey,
    ]
    last_error: Exception | None = None
    for loader in key_loaders:
        try:
            return loader.from_private_key_file(str(path), password=passphrase)
        except paramiko.ssh_exception.SSHException as exc:
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    raise ValueError(f"Could not load private key at {path}")


def build_connect_kwargs(
    *,
    user: str | None,
    password: str | None,
    key: str | None,
    key_passphrase: str | None,
    port: int,
    connect_timeout: float,
) -> dict[str, Any]:
    """Build Paramiko connect kwargs with opinionated auth defaults."""
    resolved_user = resolve_user(user)
    resolved_password = resolve_password(password)
    resolved_passphrase = resolve_key_passphrase(key_passphrase)
    key_path = resolve_key_path(key)

    kwargs: dict[str, Any] = {
        "port": port,
        "timeout": connect_timeout,
        "banner_timeout": connect_timeout,
        "auth_timeout": connect_timeout,
    }
    if resolved_user is not None:
        kwargs["username"] = resolved_user

    if key_path is not None:
        kwargs["pkey"] = load_private_key(key_path, resolved_passphrase)
        kwargs["look_for_keys"] = False
        kwargs["allow_agent"] = False
        if resolved_password is not None:
            kwargs["password"] = resolved_password
        return kwargs

    default_key = discover_default_key()
    if default_key is not None and resolved_password is None:
        kwargs["pkey"] = load_private_key(default_key, resolved_passphrase)
        kwargs["look_for_keys"] = False
        kwargs["allow_agent"] = False
        return kwargs

    if resolved_password is not None:
        kwargs["password"] = resolved_password
        kwargs["look_for_keys"] = True
        kwargs["allow_agent"] = True
        return kwargs

    kwargs["look_for_keys"] = True
    kwargs["allow_agent"] = True
    return kwargs
