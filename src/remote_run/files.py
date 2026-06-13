"""Upload and download files over SFTP."""

from __future__ import annotations

from remote_run import connection
from remote_run.auth import resolve_host
from remote_run.errors import RemoteRunError, wrap_paramiko_error


def upload(
    host: str | None,
    local_path: str,
    remote_path: str,
    *,
    user: str | None = None,
    key: str | None = None,
    password: str | None = None,
    key_passphrase: str | None = None,
    port: int = 22,
    connect_timeout: float = connection.DEFAULT_CONNECT_TIMEOUT,
) -> None:
    """Upload a local file to a remote path over SFTP.

    Examples:
        >>> from remote_run import upload
        >>> upload("203.0.113.10", "dist/app.zip", "/var/www/app.zip", user="deploy")
    """
    resolved_host = resolve_host(host)
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
            connection.transfer_file(
                client,
                local_path=local_path,
                remote_path=remote_path,
                upload=True,
            )
    except RemoteRunError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise wrap_paramiko_error(
            exc,
            context=f"SFTP upload to {resolved_host}",
        ) from exc


def download(
    host: str | None,
    remote_path: str,
    local_path: str,
    *,
    user: str | None = None,
    key: str | None = None,
    password: str | None = None,
    key_passphrase: str | None = None,
    port: int = 22,
    connect_timeout: float = connection.DEFAULT_CONNECT_TIMEOUT,
) -> None:
    """Download a remote file to a local path over SFTP.

    Examples:
        >>> from remote_run import download
        >>> download("203.0.113.10", "/var/log/nginx/error.log", "./error.log")
    """
    resolved_host = resolve_host(host)
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
            connection.transfer_file(
                client,
                local_path=local_path,
                remote_path=remote_path,
                upload=False,
            )
    except RemoteRunError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise wrap_paramiko_error(
            exc,
            context=f"SFTP download from {resolved_host}",
        ) from exc
