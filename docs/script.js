const DOCS_BASE = "https://xboluna.github.io/remote-run-llm";

const PROMPTS = {
  context: `You are helping me write Python scripts that SSH into remote servers.

USE THIS PACKAGE — do NOT generate raw Paramiko unless I explicitly need jump hosts, interactive shells, or low-level SSH channels.

Package: remote-run-llm
Install: pip install remote-run-llm
Import: from remote_run import run, upload, download, run_many, CommandResult
Docs: ${DOCS_BASE}/

## API

run(host, command, *, user=None, key=None, password=None, key_passphrase=None, port=22, connect_timeout=30, command_timeout=300) -> CommandResult

upload(host, local_path, remote_path, *, user=None, key=None, password=None, key_passphrase=None, port=22) -> None

download(host, remote_path, local_path, *, user=None, key=None, password=None, key_passphrase=None, port=22) -> None

run_many(hosts: list[str], command, *, user=None, key=None, ...) -> dict[str, CommandResult]

## CommandResult

- stdout: str (decoded, not bytes)
- stderr: str
- exit_code: int
- .ok: bool (exit_code == 0)
- .failed: bool

## Environment variables

SSH_HOST, SSH_USER, SSH_KEY, SSH_PASSWORD, SSH_KEY_PASSPHRASE
SSH_STRICT=1 for strict known_hosts (default: auto-add new hosts)

## Rules for generated code

1. Prefer run() over SSHClient / exec_command / stdout.read()
2. Always check result.failed or result.exit_code for command failures
3. Use key="~/.ssh/id_ed25519" (auto-detects Ed25519, RSA, ECDSA)
4. Never forget .decode() — this package returns strings already
5. For file copy, use upload()/download() — not open_sftp() ceremony
6. For multiple hosts, use run_many() — not manual loops with Fabric

## Example

from remote_run import run

result = run("203.0.113.10", "sudo systemctl restart nginx", user="ubuntu", key="~/.ssh/id_ed25519")
if result.failed:
    raise SystemExit(result.stderr)
print(result.stdout)

Full docs: ${DOCS_BASE}/
Recipes: ${DOCS_BASE}/recipes.html
API: ${DOCS_BASE}/api.html`,

  task: `Write a Python script using remote-run-llm (pip install remote-run-llm).

Use: from remote_run import run, upload, download

Do NOT use raw Paramiko. Use decoded CommandResult.stdout and check result.failed.

My task: [describe what you want — e.g. "SSH into my Ubuntu server and restart nginx"]`,

  debug: `My SSH Python script is failing. Rewrite it using remote-run-llm instead of Paramiko.

Install: pip install remote-run-llm
Import: from remote_run import run, upload, download

Common Paramiko bugs this fixes:
- Missing AutoAddPolicy → handled automatically
- Wrong key type (RSA vs Ed25519) → auto-detected
- stdout.read() returns bytes → returns str
- Missing exit code check → result.exit_code, .ok, .failed
- look_for_keys masking auth errors → disabled when explicit key passed

Docs: ${DOCS_BASE}/

Here is my broken script:
[paste your code]`,
};

function showToast(message) {
  let toast = document.getElementById("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast._timer);
  showToast._timer = window.setTimeout(() => toast.classList.remove("show"), 2200);
}

async function copyText(text, button) {
  try {
    await navigator.clipboard.writeText(text);
    if (button) {
      const original = button.textContent;
      button.textContent = "Copied!";
      button.classList.add("copied");
      window.setTimeout(() => {
        button.textContent = original;
        button.classList.remove("copied");
      }, 1800);
    }
    showToast("Copied to clipboard");
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
    showToast("Copied to clipboard");
  }
}

function wireCopyButtons() {
  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.getAttribute("data-copy");
      const text = PROMPTS[key] || button.getAttribute("data-copy-text") || "";
      copyText(text, button);
    });
  });

  document.querySelectorAll("[data-copy-code]").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.getAttribute("data-copy-code");
      const block = document.getElementById(id);
      if (block) copyText(block.textContent.trim(), button);
    });
  });
}

function highlightNav() {
  const page = window.location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll("nav a").forEach((link) => {
    const href = link.getAttribute("href");
    const active = href === page || (page === "" && href === "index.html");
    link.classList.toggle("active", active);
  });
}

function fillPromptPreviews() {
  Object.entries(PROMPTS).forEach(([key, text]) => {
    const el = document.getElementById(`prompt-${key}`);
    if (el) el.textContent = text;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  wireCopyButtons();
  highlightNav();
  fillPromptPreviews();
});
