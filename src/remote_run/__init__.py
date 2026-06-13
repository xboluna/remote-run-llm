"""Run SSH commands and copy files — without Paramiko boilerplate."""

from remote_run.batch import run_many
from remote_run.files import download, upload
from remote_run.result import CommandResult
from remote_run.run import run

__all__ = ["CommandResult", "download", "run", "run_many", "upload"]
__version__ = "0.1.1"
