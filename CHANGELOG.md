# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-13

### Added

- `run()` — run a command on a remote host over SSH
- `upload()` / `download()` — copy files over SFTP without managing two clients
- `run_many()` — run the same command on multiple hosts in parallel
- `CommandResult` with decoded `stdout`/`stderr`, `exit_code`, `.ok`, `.failed`
- Auto-detect Ed25519, RSA, and ECDSA private keys
- Opinionated defaults: `AutoAddPolicy`, explicit-key auth isolation, sensible timeouts
- Environment variable fallbacks: `SSH_HOST`, `SSH_USER`, `SSH_KEY`, `SSH_PASSWORD`, `SSH_KEY_PASSPHRASE`
- Strict host-key mode via `SSH_STRICT=1`

[0.1.0]: https://github.com/xboluna/remote-run-llm/releases/tag/v0.1.0
