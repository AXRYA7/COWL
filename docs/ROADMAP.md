# COWL — Development Roadmap

This document outlines the phased development roadmap for COWL, tracking milestones from initial reverse engineering research to production deployment.

---

## Phase 0: Repository Foundation & Governance
Establish repository standards, safety constraints, architectural boundaries, and legal guidelines.

- [x] Repository layout and documentation setup (`README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`).
- [x] Project specifications, roadmap, and architectural blueprint in `docs/`.
- [x] Establishment of strict safety guardrails (no speculative writes, read-only exploration first).
- **Status:** `COMPLETED`

---

## Phase 1: Safe Device Identification & Descriptor Analysis
Discover and catalog hardware identifiers using safe, read-only inspection.

- [x] Build non-destructive enumeration probe in [`tools/device-probe/probe.py`](../tools/device-probe/probe.py).
- [x] Identify Vendor ID (VID), Product ID (PID), and Interface numbers for Kreo Mirage (`045E:028E` and `054C:05C4`).
- [x] Dump and parse raw HID report descriptors (`64-byte Input`, `32-byte Output`, `64-byte Feature`).
- [x] Document endpoint configurations and report lengths in [`docs/research/mirage_device_probe_report.md`](research/mirage_device_probe_report.md).
- **Status:** `COMPLETED` (Documented in EXP-001)

---

## Phase 2: Traffic Capture & Protocol Analysis
Analyze legitimate device communication and mode-switch mechanisms through clean-room observation.

- [x] Build live mode transition monitor (`tools/device-probe/mode_monitor.py`).
- [x] Capture and record physical mode switch event dynamics on Windows USB bus (EXP-002).
- [x] Investigate software-driven mode switch feasibility (EXP-003).
- [x] Audit official Kreo Kontrol WebHID codebase & downloads ecosystem (EXP-004).
- [x] Evaluate host-side mode-switch architecture and ShanWan ODM firmware behaviors (EXP-005).
- **Status:** `COMPLETED` (Documented in EXP-002, EXP-003, EXP-004, EXP-005)

---

## Phase 3: Core Protocol Engine & Mock Testing
Build the core protocol engine in [`core/`](../core/) based on verified findings.

- [x] Implement DualShock 4 report parser & normalizer in [`core/protocol.py`](../core/protocol.py).
- [x] Implement unit test suite in [`tests/test_bridge_mapping.py`](../tests/test_bridge_mapping.py).
- [x] Verify neutral state, digital face buttons, D-pad hat switches, triggers, and thumbsticks.
- [x] 100% test pass rate across synthetic and parsed report frames.
- **Status:** `COMPLETED`

---

## Phase 4: Low-Latency Virtual Controller Bridge
Deliver real-time ViGEmBus controller emulation with sub-millisecond responsiveness.

- [x] Build multi-mode controller bridge in [`core/bridge.py`](../core/bridge.py).
- [x] Implement non-blocking queue draining to eliminate Windows HID buffer lag (<1ms latency).
- [x] Decouple connection monitoring from fast input polling loop (1000 Hz throughput).
- [x] Implement end-to-end integration and lifecycle tests in [`tests/test_cowl_integration.py`](../tests/test_cowl_integration.py).
- **Status:** `COMPLETED`

---

## Phase 5: Application / UI Layer
Deliver an intuitive, lightweight desktop application in [`app/`](../app/).

- [x] Build zero-bloat native desktop GUI in [`app/gui.py`](../app/gui.py) using pure Python & Tkinter.
- [x] Implement connection state monitor and 1-click `[ Virtual Xbox 360: ON / OFF ]` toggle switch.
- [x] Add decoupled 30 FPS live hardware diagnostics (thumbsticks, triggers, active buttons).
- [x] Provide one-click root launcher (`run_cowl.py`).
- [x] Document HidHide device cloaking setup to eliminate double-input conflicts.
- **Status:** `COMPLETED`

---

## Phase 6: Future Enhancements & Multi-Device Extensibility
Expand capabilities and support for additional peripherals.

- [ ] Add customizable deadzone and stick response curve calibration in GUI.
- [ ] Add RGB lightbar color customization (via DualShock 4 Output Report `0x05`).
- [ ] Add dual-motor haptic feedback pass-through from ViGEmBus to physical controller.
- [ ] Explore Linux (`uinput` / `evdev`) and macOS transport implementations.
- [ ] Generalize device abstraction layer (HAL) for third-party clone gamepads.
- **Status:** `PLANNED`
