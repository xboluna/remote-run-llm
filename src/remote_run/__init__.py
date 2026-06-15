"""Run SSH commands and copy files — without Paramiko boilerplate."""

from remote_run.batch import run_many
from remote_run.files import download, upload
from remote_run.result import CommandResult
from remote_run.run import run
from remote_run.script import run_script

__all__ = ["CommandResult", "download", "run", "run_many", "run_script", "upload"]
__version__ = "0.2.0"
