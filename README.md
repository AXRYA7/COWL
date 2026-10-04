<div align="center">

# 🎮 COWL

### *Hardware, under your command.*

**An ultra-low latency, zero-bloat hardware bridge & software mode switcher for the Kreo Mirage controller.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4.svg?logo=windows&logoColor=white)](https://www.microsoft.com/)
[![Driver: ViGEmBus](https://img.shields.io/badge/Driver-ViGEmBus-00C853.svg)](https://github.com/nefarius/ViGEmBus)
[![Tests: Passing](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](tests/)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](CONTRIBUTING.md)

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [HidHide Setup](#-zero-double-input-hidhide-setup) • [Research Logs](#-empirical-research-foundation) • [Contributing](#-contributing)

</div>

---

## 💡 The Problem & The Solution

The **Kreo Mirage Wireless/Wired Controller** is an agile multi-mode gamepad built on the ShanWan ODM ecosystem. However, on PC it presents significant operational hurdles:
1. **No Official PC Software:** Kreo provides no desktop configuration utility; its browser-based *Kreo Kontrol* suite supports only keyboards and mice.
2. **Awkward Hardware Button Chording:** Switching between DirectInput and XInput requires holding physical buttons for 3–5 seconds or unplugging the USB cable while holding face buttons.
3. **Double-Input & Game Incompatibilities:** Many PC games and Steam default to whichever device is detected first, causing controller conflicts, misbound buttons, or games failing to recognize the controller as an Xbox gamepad.

**COWL fixes this completely.**

COWL is a high-performance, local-first bridge that communicates directly with the Kreo Mirage in its native PlayStation mode (`054C:05C4`), parses inputs with **sub-millisecond (< 1ms)** latency, and feeds them into the Windows gaming subsystem as a genuine **Microsoft Xbox 360 Controller** via **ViGEmBus**.

---

## ⚡ Features

- **🔄 Instant 1-Click Mode Switching:** Toggle seamlessly between native PlayStation (DirectInput) and virtual Xbox 360 (XInput) modes in software—no physical button holds or cable reconnects.
- **🏎️ Sub-Millisecond Input Latency:** Non-blocking queue-draining input pipeline running at up to 1000 Hz. Stale buffered frames are flushed instantly to guarantee zero input lag.
- **🛡️ Cloaking & Zero Double-Input Conflicts:** Fully compatible with [HidHide](https://github.com/nefarius/HidHide) to cloak the physical PS4 controller from games, preventing phantom inputs and ensuring 100% of PC games detect an authentic Xbox controller.
- **🎛️ Live Visual Hardware Diagnostics:** Real-time visual readout of dual analog sticks (normalized $-1.0 \dots +1.0$), analog trigger curves, and digital button matrices.
- **🪶 Zero-Bloat Native Desktop UI:** Pure Python & Tkinter—consumes **< 30 MB RAM**, **0% idle CPU**, with zero Electron, Node.js, or browser bloat.
- **🔬 Empirical Reverse Engineering:** Built strictly upon reproducible traffic captures and documented findings (EXP-001 through EXP-005).

---

## 🏗️ Architecture

```
                                      ┌─────────────────────────────────────────┐
                                      │       Kreo Mirage Gamepad (USB)         │
                                      │    VID: 0x054C  |  PID: 0x05C4 (DS4)    │
                                      └────────────────────┬────────────────────┘
                                                           │ Raw 64-byte HID Stream
                                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  COWL Ultra-Low Latency Pipeline                                                       │
│                                                                                        │
│   ┌──────────────────────────┐      ┌──────────────────────────┐      ┌─────────────┐  │
│   │  Queue-Draining Reader   │ ───► │  core/protocol.py        │ ───► │ ViGEmBus    │  │
│   │  (Non-blocking HID read) │      │  (Report Parser & Map)   │      │ (vgamepad)  │  │
│   └──────────────────────────┘      └──────────────────────────┘      └──────┬──────┘  │
│                 │                                                            │         │
│                 ▼                                                            ▼         │
│   ┌──────────────────────────┐                               ┌──────────────────────┐  │
│   │ app/gui.py (30 FPS UI)   │                               │ Virtual Xbox 360     │  │
│   │ (Decoupled Tkinter View) │                               │ Controller           │  │
│   └──────────────────────────┘                               │ (VID: 0x045E:0x028E) │  │
│                                                              └──────────┬───────────┘  │
└─────────────────────────────────────────────────────────────────────────┼──────────────┘
                                                                          │ XInput
                                                                          ▼
                                                               ┌──────────────────────┐
                                                               │  Steam & PC Games    │
                                                               └──────────────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites

- **Windows 10 / 11** (64-bit)
- **Python 3.10+** (Tested on Python 3.13)
- **[ViGEmBus Driver](https://github.com/nefarius/ViGEmBus/releases)** (The standard virtual gamepad kernel driver):
  ```powershell
  # If you don't already have ViGEmBus installed:
  winget install --id Nefarius.ViGEmBus -e
  ```

### 2. Installation

Clone this repository and install the dependencies:

```powershell
git clone https://github.com/AXRYA7/COWL.git
cd COWL
pip install vgamepad hid
```

### 3. Launching COWL

Connect your Kreo Mirage controller (hold **Triangle** while inserting the USB cable to ensure it connects in PS4 mode `054C:05C4`), then run:

```powershell
python run_cowl.py
```

Click the **`Virtual Xbox 360 (XInput)`** toggle button. Your controller is now instantly mapped and active!

---

## 🛡️ Zero Double-Input: HidHide Setup

When using virtual controllers on Windows, modern games and Steam may detect **both** the physical PS4 controller and the virtual Xbox controller at the same time ("double-input"). 

To cloak the physical controller so games **only** see the Xbox controller:

1. **Install HidHide:**
   ```powershell
   winget install --id Nefarius.HidHide -e
   ```
   *(Or download the installer directly from [HidHide Releases](https://github.com/nefarius/HidHide/releases)).*

2. **Configure Cloaking in 30 Seconds:**
   - Open **HidHide Configuration Client** from your Windows Start menu.
   - **Applications tab:** Click `+` and whitelist your Python executable (e.g. `C:\Users\<User>\AppData\Local\Microsoft\WindowsApps\python.exe`).
   - **Devices tab:** Connect the Mirage, and check the box next to `Sony Interactive Entertainment Wireless Controller` (`054C:05C4`).
   - Check **"Enable device hiding"** at the bottom (the lock icon will close).

Games will now see **only** the Virtual Xbox 360 Controller with 100% compatibility.

---

## 🔬 Empirical Research Foundation

COWL follows strict clean-room engineering. Every feature is grounded in empirical hardware captures documented in [`docs/research/`](docs/research/):

| Experiment | Title | Core Finding | Status |
| :--- | :--- | :--- | :--- |
| **[EXP-001](docs/research/mirage_device_probe_report.md)** | Device Probe & Enumeration | Identified dual USB personalities: XInput (`045E:028E`) and DualShock 4 (`054C:05C4`). | `VERIFIED` |
| **[EXP-002](docs/research/experiments/EXP-002-mode-transition.md)** | Physical Mode Transition Dynamics | Verified that physical button chording triggers electrical USB bus detach (D+ pull-down) and full re-enumeration. | `VERIFIED` |
| **[EXP-003](docs/research/experiments/EXP-003-programmatic-mode-switch.md)** | Programmatic Mode-Switch Investigation | Confirmed mode switching is handled internally by MCU GPIO timers; Windows `xusb22.sys` blocks host-side detach commands in State 1. | `VERIFIED` |
| **[EXP-004](docs/research/experiments/EXP-004-official-software-traffic.md)** | Official Software & Ecosystem Audit | Audited `kontrol.kreo-tech.com` WebHID bundles: 0 controllers supported. Confirmed Kreo Mirage operates 100% driverless. | `VERIFIED` |
| **[EXP-005](docs/research/experiments/EXP-005-software-mode-switch.md)** | Host-Side Mode-Switch Architecture | Proved hardware USB personality toggling from host is infeasible; established Virtual Controller Emulation as the optimal, zero-lag solution. | `VERIFIED` |

---

## 🧪 Testing & Verification

COWL includes automated test suites covering protocol parsing boundaries and bridge lifecycles:

```powershell
# Run protocol decoder and mapping assertions:
python tests/test_bridge_mapping.py

# Run end-to-end integration and ViGEmBus lifecycle tests:
python tests/test_cowl_integration.py
```

All tests run headlessly without requiring physical hardware connected.

---

## 📁 Repository Structure

```text
COWL/
├── app/
│   └── gui.py                 # Sleek dark-mode desktop GUI (Tkinter)
├── core/
│   ├── bridge.py              # Ultra-low latency ViGEmBus bridge & queue drainer
│   └── protocol.py            # DualShock 4 HID report parser & normalizer
├── docs/
│   ├── ARCHITECTURE.md        # Technical architecture and component design
│   ├── PROJECT.md             # Project specification and mission statement
│   ├── ROADMAP.md             # Development roadmap and milestone gates
│   └── research/              # Empirical research findings & experiments
│       └── experiments/       # EXP-001 through EXP-005 reports
├── tests/
│   ├── test_bridge_mapping.py # Protocol and report translation unit tests
│   └── test_cowl_integration.py # End-to-end bridge lifecycle tests
├── tools/
│   └── device-probe/          # Safe read-only USB/HID diagnostic probes
├── run_cowl.py                # One-click application launcher
├── AGENTS.md                  # Safety guardrails and engineering directives
├── CONTRIBUTING.md            # Guidelines for research and code contributions
├── LICENSE                    # Apache License 2.0
├── README.md                  # Project overview (this file)
└── SECURITY.md                # Hardware security and safety policy
```

---

## 🛡️ Safety & Clean-Room Directives

Development within COWL strictly adheres to [AGENTS.md](AGENTS.md):
- **Zero Firmware Flashing:** COWL never attempts to flash, patch, dump, or modify device firmware or bootloaders.
- **Zero Arbitrary HID Writes:** All packet structures are verified and bounded before dispatch; blind fuzzing is forbidden.
- **Clean-Room Methodology:** Developed without proprietary Kreo source code, decompilation, or reverse engineering of copyrighted assets.
- **No Anti-Cheat Evasion:** COWL is purely an input translator and configuration bridge; it contains no rapid-fire, macros, or unfair advantage tools.

---

## 🤝 Contributing

Contributions, bug reports, and hardware captures are warmly welcomed! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md) before submitting pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## ⚖️ Legal Disclaimer

*COWL is an independent open-source project and is **not** affiliated with, endorsed by, or associated with Kreo, Sony Interactive Entertainment, Microsoft Corporation, or ShenZhen ShanWan Technology Co., Ltd. All product names, logos, brands, and registered trademarks are the property of their respective owners.*

---

## 📄 License

This project is licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.
