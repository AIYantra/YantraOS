# YantraOS Master Context File

## 1. Project Overview & Mission
**Project:** YantraOS
**Tagline:** The Cognitive OS for Autonomous and Legacy Hardware.
**Current Phase:** Implementation (Milestone 6: ISO Build & Daemonization).
**Description:** YantraOS is a Linux-based operating system designed to embed cognitive reasoning (LLMs, Vector Memory) at the lowest levels of the OS stack. It transforms any hardware (from old laptops to modern server racks) into an autonomous, self-managing entity capable of reasoning about its environment, health, and user intents.

## 2. Core Architecture
YantraOS is built on a custom Arch Linux foundation, orchestrated via an `archiso` pipeline. It is intentionally minimal, acting as a hypervisor for the Cognitive Engine.

**The Stack (Bottom to Top):**
1. **Kernel:** Linux `linux-lts` (stable, long-term support).
2. **Init System:** `systemd` (handles early boot, networking, and daemon lifecycle).
3. **Hardware Layer (HAL):** Btrfs for snapshotting, NetworkManager for connectivity, custom Python probes for GPU/CPU telemetry.
4. **The Daemon (`yantra.service`):** The heart of the OS. A root-level Python daemon running an orchestration loop.
5. **Cognitive Engine:** Lives within the daemon. Uses `LiteLLM` to interact with local or remote reasoning models. Maintains state via ChromaDB (Vector DB).
6. **Execution Sandbox:** A tightly restricted Docker environment where the LLM can safely execute bash commands to manage the host.
7. **User Interface (TUI):** A terminal-based HUD built with `textual`/`rich`, providing a live view into the daemon's "brain."
8. **Cloud Telemetry:** Reports node health and status to a central Next.js/Supabase dashboard.

## 3. The Yantra Daemon (`core/daemon.py`)
The daemon runs as a continuous loop, analyzing the system context and deciding on the next best action.

**The Orchestrator Loop:**
1. **Sense:** Gather telemetry (CPU, RAM, GPU, Disk, Logs).
2. **Remember:** Retrieve past actions and context from Vector Memory (ChromaDB).
3. **Reason:** Submit telemetry and context to the LLM (via LiteLLM router). The LLM determines the `next_action`.
4. **Act (Sandboxed):** Execute the `next_action`. If the action requires system modification, it is executed via SSH from a heavily restricted Docker container.
5. **Log & Learn:** Store the outcome of the action back into Vector Memory.
6. **Report:** Push a heartbeat and telemetry block to the central Cloud API.

**Security Constraints (Red Team Hardening):**
*   The daemon runs as `yantra_daemon` (UID 999), **NOT root**.
*   The LLM **CANNOT** execute commands directly on the host.
*   All LLM-generated commands are executed inside a locked-down Alpine Docker container.
*   The container has *no inherent network access* (except via a proxy if necessary) and *no root access to the host*.
*   To manage the host, the container must SSH back into the host using a restricted SSH key that only allows specific whitelisted commands (e.g., `systemctl restart`, `pacman -Syu`).

## 4. Hardware Profiles & Adaptation
YantraOS is designed to boot and adapt to disparate hardware.

*   **Alpha Node:** The "brain." Heavy compute (e.g., A100s, H100s). Runs large local models (Llama-3 70B, Qwen). Acts as a routing hub for the cluster.
*   **Edge Node:** "Sensors/Actuators." Old laptops, NUCs, Raspberry Pis. Runs tiny local models (Phi-3, Gemma-2B) or routes queries to the Alpha Node/Cloud. Focuses on local control and telemetry gathering.

**Adaptive Fallbacks:**
*   If GPU is available -> Use `llama.cpp` / local PyTorch models.
*   If GPU is absent/weak -> Fallback to Cloud APIs (OpenAI, Anthropic, Groq) via LiteLLM.
*   If Network is down -> Rely strictly on local cached models or halt non-critical ops.
*   (Implemented) If `pynvml` fails (driver missing on ISO): Use mock GPU state.
*   (Implemented) If `chromadb` fails (missing on ISO): Log warning and gracefully degrade memory storage to no-op.

## 5. Development Environment Setup
The user (`tsy`) develops on a Linux laptop. The primary workspace is `/home/admin/Documents/YantraOS`.

**Prerequisites:**
*   `mkarchiso` (Arch Linux `archiso` package)
*   Python 3.12+
*   Docker
*   QEMU (for ISO testing)

**Repository Structure:**
```
YantraOS/
├── archlive/                # ArchISO configuration
│   ├── airootfs/            # The live filesystem overlay
│   ├── build.sh             # Master build script (DEPRECATED - Use compile_iso.sh)
│   ├── compile_iso.sh       # The actual build orchestrator
│   ├── pacman.conf          # Package definitions
│   └── profiledef.sh        # ISO metadata and permissions
├── core/                    # The Yantra Cognitive Daemon
│   ├── cli.py               # The Textual TUI
│   ├── cloud.py             # Telemetry reporting
│   ├── daemon.py            # The main orchestration loop
│   ├── engine.py            # LLM interaction and reasoning logic
│   ├── hardware.py          # Telemetry gathering (CPU, RAM, GPU)
│   ├── vector_memory.py     # ChromaDB state management
│   └── sandbox/             # Docker execution environment
│       └── Dockerfile
├── deploy/                  # Systemd and Polkit configurations
├── docs/                    # Architecture diagrams and planning
└── web/                     # Next.js Cloud Dashboard
```

## 6. ISO Build Process (`compile_iso.sh`)
The ArchISO build process is fully automated via `archlive/compile_iso.sh`.

**Build Phases:**
1.  **Preparation:** Copies YantraOS core files into the `airootfs` overlay.
2.  **Dependencies:** Creates a Python `venv` inside the `airootfs` and installs required packages (FastAPI, LiteLLM, ChromaDB, etc.).
3.  **Hashbang Correction:** Rewrites the `venv` scripts to use the correct deployment path (`/opt/yantra/venv/...`) instead of the build machine's absolute path.
4.  **Configuration Injection:** Sets up systemd services, users (`yantra_daemon`), and injects secrets.
5.  **Compilation:** Runs `mkarchiso` to generate the `.iso` file.

**Usage:**
```bash
cd ~/Documents/YantraOS/archlive
sudo bash compile_iso.sh
```

## 7. Configuration & Secrets Management
*   **System Configuration:** Handled via standard Linux mechanisms (systemd, sysusers.d, tmpfiles.d).
*   **Daemon Settings:** Managed via `pydantic-settings` in `core/config.py`.
*   **Secrets:** API keys (OpenAI, Anthropic) and Telemetry tokens are injected into the ISO build via a `.env` file and placed in `/etc/yantra/secrets.env` (readable only by root/yantra_daemon).

## 8. Current State (Milestone 6)
We are currently finalizing Milestone 6: "ISO Build & Daemonization."
*   **Completed:**
    *   Basic Daemon orchestration loop.
    *   Hardware telemetry (CPU, RAM, basic mock GPU).
    *   Cloud telemetry reporting (Next.js ingest API is live).
    *   Textual TUI initialized.
    *   ArchISO infrastructure setup (`compile_iso.sh`).
*   **In Progress / Immediate Next Steps:**
    *   Finalize the Docker Sandboxing implementation.
    *   Implement the restricted SSH execution pathway back to the host.
    *   Thorough testing of the generated ISO via QEMU.
    *   Implement Btrfs autosnapshots (Snapper integration).

## 9. Next.js Cloud Dashboard (`web/`)
A central dashboard built with Next.js, TailwindCSS, and Supabase.
*   **Purpose:** Fleet management, live telemetry visualization, and manual override capabilities.
*   **Status:** Deployed on Vercel (`www.yantraos.com`).
*   **API Routes:**
    *   `POST /api/telemetry/ingest`: Receives health heartbeats from YantraOS nodes. Secured via a hardcoded bearer token (`YANTRA_TELEMETRY_TOKEN`) for now.

## 10. Key Architectural Decisions (ADRs)
*   **ADR-001: Python over Rust/Go:** Python chosen for the daemon to leverage the massive AI/ML ecosystem (LiteLLM, LangChain, PyTorch) faster, despite performance overhead. Performance-critical paths will be rewritten in Rust later.
*   **ADR-002: Docker Sandboxing:** LLM-generated commands are executed in a container, not directly on the host, to contain hallucinations and prevent catastrophic self-modification.
*   **ADR-003: Arch Linux Foundation:** Chosen for its bleeding-edge kernel and minimal base, allowing us to build exactly what we need without ripping out Ubuntu/Debian cruft.

## 11. Known Issues & Blockers
*   [ ] Full end-to-end test of the LLM -> Docker -> SSH -> Host execution loop is pending.
*   [ ] ChromaDB persistent storage needs rigorous testing across ISO reboot cycles.
*   [ ] NVIDIA driver integration on the live ISO is currently mocked; needs proper driver injection for real hardware testing.

## 12. Important Server Endpoints
*   **Cloud Ingest:** `https://www.yantraos.com/api/telemetry/ingest`
*   **Docs:** `https://www.yantraos.com/docs` (Placeholder)

## 13. System Prompts & LLM Instructions
*   When fixing code, prioritize *resilience*. If a sub-system fails (e.g., Vector DB), the core loop must continue degrading gracefully.
*   Never suggest running LLM-generated bash scripts as root on the host machine.
*   When editing the ArchISO scripts, remember that paths inside `airootfs` are relative to the final ISO, not the build machine. 

## 14. Fixes to ISO Deployment (Milestone 6 Verification Stage)
On 2/25/2026, the ISO compilation (`compile_iso.sh`) was audited and hardened for QEMU testing.
*   We resolved python path expansion failures where build-server paths leaked into ISO binaries (`pip`, `uvicorn`, etc.). 
*   Implemented precise sed replacements across `venv/bin` binaries locking python to `#!/opt/yantra/venv/bin/python3`.
*   Validated the `.archiso-tmp` state removal and enforced `chown -R root:root` of the parent tree before `mkarchiso` generation. 

## 15. Core Infra, ISO Build, and Kiosk Fixes (Feb-Mar 2026)
In our final push for a stable ISO boot, the following critical architecture patches were applied:

1. **Vector Memory Asynchronous Integrity (`core/vector_memory.py`)**
   - **The Bug:** ChromaDB initialization was synchronous, blocking the `asyncio` loop running the orchestrator, and failing the build when pip packages were misaligned.
   - **The Fix:** Migrated `initialize()` and `_require_initialized()` to full asynchronous execution. Implemented a `self._init_failed` graceful degradation handle so the daemon continues tracking telemetry even if ChromaDB fails, instead of spamming loop failures.

2. **Telemetry Payload Re-arming (`core/cloud.py` & Vercel API)**
   - Vercel's Edge ingest API (`api/telemetry/ingest`) was successfully re-armed to check the `Authorization` header against the `YANTRA_TELEMETRY_TOKEN`. 
   - Modified `cloud.py` to correctly inject `Bearer <TOKEN>` on egress.

3. **Global Secrets Alignment (`host_secrets.env`)**
   - Migrated from generic `.env` tracking to a formal `host_secrets.env` payload definition. This securely injects the Telemetry Token, API keys, and model overrides during the ArchISO setup phase. Ignored in Git.

4. **ArchISO Build Hardening (`compile_iso.sh`)**
   - **TMPFS Exhaustion (`No space left on device`):** Redirected `mkarchiso`'s temporary working directory to a physical drive path (`/home/admin/Documents/YantraOS/work`) instead of `/tmp/archiso-tmp`.
   - **Pip Installation Stability:** Added `--retries 10 --timeout 120` to all pip operations within the airootfs loop to tolerate network flakiness.
   - **ISO Boot Scripts (Permissions):** Specifically allowed `["/root/.automated_script.sh"]="0:0:0755"` in `compile_iso.sh` because the Arch build process was overriding the `profiledef.sh` edits.

5. **Yantra User & Cage Wayland Initialization**
   - **The Bug:** `su - yantra_user` failed on boot because the user directory wasn't created, meaning the TUI kiosk (Cage/Wayland) crashed with a missing `DQUANTUM_ID` environment context.
   - **The Fix:**
     * Interjected `airootfs/etc/passwd` and `airootfs/etc/group` with static `yantra_user` (UID 1000) defaults.
     * Modified `compile_iso.sh` to physically `mkdir -p /home/yantra_user` and map its permissions via the script's core `file_permissions` array.
     * Augmented the `su - yantra_user` login routine to manually forge `XDG_RUNTIME_DIR=/run/user/1000` prior to evaluating the `cage` compositor.