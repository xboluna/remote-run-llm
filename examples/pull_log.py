"""Pull a remote log file to the local machine."""

from remote_run import download

download(
    "203.0.113.10",
    "/var/log/nginx/error.log",
    "./error.log",
    user="ubuntu",
)

print("Saved remote log to ./error.log")
