"""Deploy a build artifact to a remote server."""

from remote_run import upload

upload(
    "203.0.113.10",
    "dist/app.zip",
    "/var/www/app.zip",
    user="deploy",
    key="~/.ssh/id_ed25519",
)

print("Uploaded dist/app.zip -> /var/www/app.zip")
