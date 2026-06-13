# remote-run-llm


Paramiko is a strong wrapper target because the jobs people want are simple, but the library forces you to think like an SSH protocol implementer. That gap is exactly where non-technical / vibe-coding users get stuck — and where LLMs produce code that looks right but fails in subtle ways.
What people actually use Paramiko for
From docs, tutorials, and community pain, usage clusters into a few buckets:
Use case	Share of "I just want to…" requests	Paramiko surface today
Run one remote command	~60–70%	SSHClient → connect() → exec_command() → read byte streams → decode → check exit status → close()
Upload / download files (SFTP)	~20–25%	Same connect dance → open_sftp() → put()/get() → two clients to close
Run on several servers	~10%	Repeat above N times, or reach for Fabric
Interactive shell	~5%	invoke_shell() — rare in LLM-generated scripts
Bastion / jump host	Power users only	sock= tunneling — LLMs almost never get this right
The scanner flagged Paramiko because it has 115M monthly downloads, a deep class hierarchy (71 classes, depth 4), and credential/key friction — but the human intent behind most of those downloads is really just three verbs:
connect → run → (maybe) copy a file
Everything else is accidental complexity.
How non-technical people use Paramiko when coding with LLMs
They don't say "I need an SSHv2 client." They say things like:
"SSH into my server and restart nginx"
"Deploy this config.json to /etc/myapp/"
"Run df -h on my DigitalOcean droplet"
"Pull /var/log/app.log to my laptop"
Their mental model is ssh user@host 'command' — not transports, channels, host-key policies, or key-type classes.
What they typically have:
A hostname/IP (often pasted from a cloud dashboard)
A username (root, ubuntu, deploy)
Either a password or a key path (~/.ssh/id_rsa)
Sometimes nothing explicit — they assume "it works like Terminal"
What they don't have:
An opinion on AutoAddPolicy vs RejectPolicy
Knowledge of RSA vs Ed25519 key classes
Distinction between login password and key passphrase
Patience for stdout.read().decode() and channel.recv_exit_status()
So they ask an LLM, get a 15-line Paramiko snippet, and hit one of the classic failure modes.
Where LLMs break on raw Paramiko (core friction points)
These are the bugs that eat hours and aren't "user error":
Host key policy — Forgetting set_missing_host_key_policy(AutoAddPolicy()) → SSHException on first connect to a new server (very common in dev).
Key type guessing — LLMs default to paramiko.RSAKey.from_private_key_file(...) even when the key is Ed25519 or ECDSA.
Passphrase vs password confusion — Encrypted key needs passphrase at key load time; connect(password=...) is for login password. Mixing these produces misleading PasswordRequiredException.
look_for_keys=True masking failures — When explicit key auth fails, Paramiko silently tries ~/.ssh/id_rsa. If that's encrypted, you get a confusing exception that hides the real auth problem. Fix: look_for_keys=False, allow_agent=False when passing an explicit key.
Byte streams, not strings — stdout.read() returns bytes; LLM code forgets .decode() or checks output wrong.
No exit code — exec_command doesn't tell you if the command failed unless you call channel.recv_exit_status().
Connection lifecycle — Missing close() or context manager → hanging processes (Paramiko docs literally warn about this).
Algorithm mismatches — Older servers need disabled_algorithms={'pubkeys': ['rsa-sha2-512', 'rsa-sha2-256']}; LLMs never generate this.
Two-client SFTP dance — Users want upload(file) but get open_sftp() lifecycle management.
Fabric already wraps much of this — but LLMs still emit raw Paramiko constantly (it's in more Stack Overflow answers and older tutorials). Fabric also still exposes connect_kwargs, gateways, and Invoke's config model — more than a vibe-coder needs.
Specific wrapper(s) that would directly address this
I'd think in terms of one package, three entry points — not a generic "Paramiko but easier" rewrite.
1. remote-run — the 70% case
One function, one job.
from remote_run import run
result = run("203.0.113.10", "sudo systemctl restart nginx", user="ubuntu", key="~/.ssh/id_ed25519")
print(result.stdout)
if result.failed:
    raise SystemExit(result.stderr)
Opinionated defaults baked in:
Auto-detect key type from file header (Ed25519 / RSA / ECDSA)
AutoAddPolicy in dev; strict known_hosts when SSH_STRICT=1
look_for_keys=False when key is explicit
Returns decoded strings + exit_code + .ok / .failed properties
Sensible timeouts (connect 30s, command 5min)
Context manager hidden — connection always closed
Env fallbacks: SSH_HOST, SSH_USER, SSH_KEY, SSH_PASSWORD, SSH_KEY_PASSPHRASE
This is what LLMs think they're generating when they write Paramiko.
2. remote-files — the 25% case
Same auth/connect logic, different verbs:
from remote_run import upload, download
upload("203.0.113.10", "dist/app.zip", "/var/www/app.zip", user="deploy")
download("203.0.113.10", "/var/log/nginx/error.log", "./error.log")
No SFTPClient in the public API. No separate "open sftp then close ssh" ceremony.
3. remote-run batch mode — the 10% case (optional v2)
from remote_run import run_many
results = run_many(["web1", "web2", "web3"], "apt-get update", user="root", key="~/.ssh/id_ed25519")
Fabric's Group does this, but a minimal parallel runner without Invoke/Fabric's task framework is still underserved for LLM codegen — Fabric imports and config are themselves a bit much for a 20-line script.
What the interface should be opinionated about
These are high-inertia choices worth making explicitly and documenting:
Decision	Opinion	Why
Host keys	AutoAddPolicy by default; opt-in strict mode	Vibe-coders hit new VPS constantly; they don't manage known_hosts
Auth	Args → env vars → ~/.ssh/id_ed25519 then id_rsa	Matches how Terminal "just works"
Explicit key passed	Disable agent + look_for_keys	Prevents the #1 misleading error cascade
Return type	CommandResult(stdout, stderr, exit_code) strings	LLMs and humans both expect printable output
Errors	Wrap Paramiko exceptions with fixes	"Key is encrypted — set SSH_KEY_PASSPHRASE or pass key_passphrase="
API shape	Functions, not classes	LLMs generate run(host, cmd) reliably; they fumble SSHClient lifecycle
Sync only	No async in v1	99% of scripts are synchronous; async adds codegen failure modes
No Transport escape hatch in v1	paramiko stays a dependency, not re-exported	Forces the 99% path; power users can still import paramiko
Jump hosts	v2 or explicit via="bastion.example.com"	Don't expose sock= — LLMs can't handle it
What not to wrap (the 1% that isn't your product)
Transport / low-level channels
SSH server mode
invoke_shell() interactive sessions
SFTP chmod / chown / symlinks
Custom ProxyCommand strings
If someone needs these, they should use Paramiko or Fabric directly. Your wrapper wins by refusing to be general.
Positioning vs Fabric
Fabric	Your wrapper
Target user	DevOps / sysadmins	LLM-assisted scripters, beginners
API	Connection, Group, tasks, fab CLI	3 functions: run, upload, download
Config	Invoke config files, connect_kwargs	Env vars + function args only
Mental model	"Pythonic deployment tool"	"ssh but from a script"
Dependency weight	paramiko + invoke	paramiko only
Fabric is the right tool for multi-host deployment workflows. Your opportunity is the single-shot script that a non-technical person generates in Cursor and expects to run once.
Bottom line
Paramiko users (especially via LLMs) want:
Run a command on a remote machine
Maybe copy a file
With credentials they already have in env or ~/.ssh
They don't want to learn host-key policies, key-type classes, stream decoding, or exit-status channels.
A package like remote-run (name TBD) that depends on Paramiko and exports:
run(host, command, *, user=None, key=None, password=None, key_passphrase=None, port=22, timeout=300)
upload(host, local_path, remote_path, ...)
download(host, remote_path, local_path, ...)
…with aggressive defaults and human-readable errors would cover ~99% of LLM-generated Paramiko use and directly attack every friction point our scanner surfaced.
