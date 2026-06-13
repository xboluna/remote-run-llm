"""Run the same command on multiple web servers."""

from remote_run import run_many

results = run_many(
    ["web1.example.com", "web2.example.com", "web3.example.com"],
    "uptime",
    user="root",
    key="~/.ssh/id_ed25519",
)

for host, result in results.items():
    print(f"{host}: {result.stdout.strip()} ({'ok' if result.ok else 'failed'})")
