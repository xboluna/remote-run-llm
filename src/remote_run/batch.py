"""Run commands on multiple hosts in parallel."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from remote_run.result import CommandResult
from remote_run.run import run


def run_many(
    hosts: list[str],
    command: str,
    *,
    user: str | None = None,
    key: str | None = None,
    password: str | None = None,
    key_passphrase: str | None = None,
    port: int = 22,
    max_workers: int | None = None,
) -> dict[str, CommandResult]:
    """Run the same command on multiple hosts in parallel.

    Returns a mapping of host -> CommandResult in completion order is not
    preserved; iterate hosts explicitly when order matters.

    Examples:
        >>> from remote_run import run_many
        >>> results = run_many(["web1", "web2"], "hostname", user="root")
        >>> results["web1"].stdout
    """
    if not hosts:
        return {}

    worker_count = max_workers or min(32, len(hosts))
    results: dict[str, CommandResult] = {}

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(
                run,
                host,
                command,
                user=user,
                key=key,
                password=password,
                key_passphrase=key_passphrase,
                port=port,
            ): host
            for host in hosts
        }
        for future in as_completed(future_map):
            host = future_map[future]
            results[host] = future.result()

    return results
