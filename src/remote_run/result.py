"""Command execution result."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    """Result of a remote command execution."""

    stdout: str
    stderr: str
    exit_code: int
    host: str
    command: str

    @property
    def ok(self) -> bool:
        """True when the remote command exited with status 0."""
        return self.exit_code == 0

    @property
    def failed(self) -> bool:
        """True when the remote command exited with a non-zero status."""
        return not self.ok
