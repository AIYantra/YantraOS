# yantraOS

> An Arch Linux-based research system for building safer, human-supervised AI actions on a personal computer.

```text
YOUR OS HAS BEEN PASSIVE FOR TOO LONG.

The computer was always capable of thinking.
We just never asked it to.

— yantraOS
```

yantraOS explores a simple question: what would it take for a computer to understand an instruction, choose the least expensive reliable way to carry it out, and stay inside clear security boundaries?

The answer is not unrestricted shell access. yantraOS separates unprivileged reasoning, bounded desktop automation, a root-only sandbox broker, typed host intents, confirmation, audit records, and BTRFS recovery points.

**Current community release:** the M7 signed live-boot ISO. It has been manually verified in QEMU. Treat it as an early, disposable-system release, not a daily-driver operating system.

| | |
|---|---|
| License | [MIT](LICENSE) |
| Foundation | Arch Linux, systemd, Python |
| Current release track | M7 signed live image |
| Public installer | Not released yet |

## What Works Today

The following is verified project evidence, not a promise of universal hardware support:

| Capability | Current state |
|---|---|
| Signed ArchISO and fixed Azure VHD | Built and booted in QEMU; Azure provisioning was manually validated. |
| Deterministic action routing | File creation/moves and known app launches can select a CLI fast path rather than a visual loop. |
| Visual computer use | Browser and desktop workflows were manually verified on the supported KDE/Wayland test setup. |
| Bounded file management | Create, read, and no-overwrite move operations are confined to `~/Documents/YantraOS`. |
| Privileged boundary | The root executor accepts a typed restart of `yantra.service`; arbitrary shell commands are rejected. |
| Sandboxed generated scripts | A root-owned broker runs a fixed Docker policy with no network or host mounts. |
| Local control plane | The daemon exposes a loopback-only HTTP API at `127.0.0.1:50000`. |

Desktop automation requires an active logged-in desktop session. It fails closed without one.

## Release Status

### Available today

- The M7 community live image and its signed checksum.
- The source tree, security regression tests, ISO forge, and Azure fixed-VHD forge.
- The core action, confirmation, audit, sandbox, and host-executor boundaries.

### In development

- The M8 personal-PC installer path. It is being validated on disposable systems and will be published separately only after real non-primary-machine usage.
- Broader hardware and boot-mode coverage for the installer.

### Future vision

- A hosted runtime.
- A browser-accessible experience.
- A skill marketplace, only after sandbox and remote-revocation requirements are met.

Those are roadmap items, not current product capabilities.

## How It Works

yantraOS intentionally does not present one unchecked model output as a system command. Its active paths are separate and narrow:

```text
Natural-language instruction
          |
          v
Action classification and confirmation
          |
          +--> Deterministic fast path
          |      Bounded file actions or known app launches
          |
          +--> Desktop automation
          |      Screenshot -> one action -> visible verification
          |      Runs in the logged-in user session
          |
          +--> Generated script
                 Unprivileged client -> root sandbox broker -> Docker

Typed host intent
          |
          v
/run/yantra/executor.sock -> root executor -> allowlisted operation
```

Alongside those action paths, `yantra.service` runs the core daemon as `yantra_daemon`. Its current execution loop is `SENSE -> REASON -> ACT`, and its state/control API binds only to `127.0.0.1:50000`.

## Security Model

The security posture is intentionally conservative:

- `yantra_daemon` is unprivileged and has no Docker-group access.
- The Docker broker is root-owned; it authorizes the daemon through Unix peer credentials.
- Sandbox containers have no network, no host mounts, a read-only root filesystem, no Linux capabilities, `no-new-privileges`, and bounded CPU, memory, PID, output, and execution time.
- The host executor uses typed JSON, explicit argument arrays, strict field validation, peer credential checks, and BTRFS preflight snapshots where applicable.
- Confirmation and audit hooks surround external actions.
- Runtime credentials belong in root-owned service environment files, never in Git or the ISO image.

Desktop actions are deliberately not described as sandboxed. They operate in a real user session and therefore require explicit confirmation, visible verification, and audit coverage.

## Boot the Community ISO

Use a disposable VM or non-primary machine. The M7 image is a **live boot** release; do not treat it as the public personal-PC installer.

After downloading an ISO, checksum, and signature from [GitHub Releases](https://github.com/AIYantra/YantraOS/releases), verify the checksum from the directory that contains them:

```bash
sha256sum -c yantraos-*.iso.sha256
```

Test a single downloaded ISO in QEMU:

```bash
qemu-system-x86_64 \
  -m 4G \
  -enable-kvm \
  -cpu host \
  -cdrom yantraos-*.iso \
  -boot d
```

The live image intentionally does not carry operational secrets. Follow `.env.example` and the release instructions to provision valid runtime credentials. Never commit a populated `.env` file.

## Run From Source

The development environment needs Python 3.12, Docker for sandbox checks, and valid provider credentials for real model-backed actions.

```bash
git clone https://github.com/AIYantra/YantraOS.git
cd YantraOS

python3 -m venv venv
venv/bin/pip install --require-hashes -r requirements.lock

# Create a private local environment file and supply valid values before real actions.
cp .env.example .env
chmod 600 .env
```

At minimum, `YANTRA_CONTROL_TOKEN` must be a valid value of 32 or more characters. Azure-backed paths also require the relevant values from `.env.example`.

Useful entry points:

```bash
# Core daemon. Requires a valid runtime environment.
venv/bin/python -m core.daemon

# Natural-language action path. Requires a configured provider and desktop session where applicable.
venv/bin/python -m core.yantra_core "create a project brief in Documents/YantraOS"

# Native desktop shell. Run only in an active desktop session.
venv/bin/python -m ui.gui_shell
```

Read-only local diagnostics:

```bash
curl http://127.0.0.1:50000/health
curl http://127.0.0.1:50000/state
systemctl status yantra.service yantra-sandbox-broker.service yantra-host-executor.service
```

## Build a Development ISO

The forge is for Arch Linux maintainers. It builds a sandbox image, a Python environment, a locally built checksum-pinned Calamares package, and a signed ISO.

```bash
sudo pacman -S --needed \
  archiso btrfs-progs squashfs-tools arch-install-scripts \
  rsync gnupg docker devtools pacman-contrib

sudo systemctl enable --now docker

read -r -p "Ed25519 signing-key path: " YANTRA_SIGNING_KEY
export YANTRA_SIGNING_KEY
sudo -E ./archlive/forge_sovereign_iso.sh
```

Artifacts are written to `/opt/yantra-releases/` as an ISO with matching `.sha256` and `.sha256.sig` files.

Do not publish a locally built installer image as a release until it has passed fresh-install and non-primary-machine validation.

## Development Checks

Prefer focused deterministic checks. Some root-level test files are manual or can invoke live integrations, so do not run every `test_*.py` blindly on a workstation.

```bash
venv/bin/python -m unittest test_computer_use_bridge.py
venv/bin/python -m pytest -p no:cacheprovider test_external_action.py
venv/bin/python test_deployment_security.py
venv/bin/python -m unittest test_installer_profile.py

venv/bin/python -m py_compile core/computer_use_bridge.py core/yantra_core.py
bash -n archlive/forge_sovereign_iso.sh
```

CI additionally runs linting, the regression suite, deployment policy checks, shell syntax checks, and a sandbox-image build.

## Project Map

```text
archlive/       Signed ArchISO profile and forge
cloud/          Fixed VHD forge and Azure deployment tooling
core/           Daemon, action routing, sandbox, audit, and host executor
deploy/         systemd units, sysusers, and tmpfiles policy
scripts/        Provisioning and maintenance helpers
ui/             PySide6 desktop shell and prototype interface
test_*.py       Focused security and integration regression tests
```

## Contributing

Contributions are welcome when they strengthen a verified path rather than introduce speculative surface area.

Before opening a pull request:

1. Start from `main` and keep the change focused.
2. Add or update the smallest deterministic test that protects the behavior.
3. Preserve the trust boundaries: no raw privileged shell strings, no Docker access for `yantra_daemon`, no credential commits, and no bypass around confirmation or audit.
4. Run the relevant focused checks.
5. Document user-visible changes accurately.

The current scope is intentionally narrow. Hosted runtime, marketplace, billing, and broader fleet work are not contribution targets until their roadmap conditions are met.

See [CONTRIBUTING.md](CONTRIBUTING.md) for issue and pull-request guidance.

## FAQ

### Is yantraOS a general-purpose Linux distribution?

Not yet. It is an Arch-based research and systems project with a validated live-image path. The personal-PC installer is still under release validation.

### Does yantraOS give an LLM unrestricted root access?

No. The root executor is typed and allowlisted. In the current implementation, its supported host operation is restarting `yantra.service`; arbitrary host commands are rejected.

### Does every action run in Docker?

No. Model-generated scripts use the hardened Docker broker. Desktop automation necessarily runs in the logged-in desktop session and has separate confirmation, audit, and visible-verification safeguards.

### Can I install software or manage windows through it today?

Those are not verified community-release capabilities yet. Software installation, window management, and long-running task management remain unchecked in the project checklist.

## License

yantraOS is released under the [MIT License](LICENSE). Copyright 2026 Euryale Ferox Private Limited.
