# COWL — Development Roadmap

This document outlines the phased development roadmap for COWL, starting from foundation setup to full controller configuration support.

Each phase has strict completion criteria and safety gates. Development must not jump ahead of verified research.

---

## Phase 0: Repository Foundation & Governance *(Current)*
Establish repository standards, safety constraints, architectural boundaries, and legal guidelines.

- [x] Repository layout and documentation setup (`README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`).
- [x] Project specifications, roadmap, and architectural blueprint in `docs/`.
- [x] Establishment of strict safety guardrails (no speculative writes, read-only exploration first).

---

## Phase 1: Safe Device Identification & Descriptor Analysis
Discover and catalog hardware identifiers using safe, read-only inspection.

- [ ] Build non-destructive enumeration probe in [`tools/device-probe/`](../tools/device-probe/).
- [ ] Identify Vendor ID (VID), Product ID (PID), and Interface numbers for Kreo Mirage across connection types (USB wired, 2.4GHz dongle, Bluetooth).
- [ ] Dump and parse raw HID report descriptors.
- [ ] Document endpoint configurations and report lengths in [`docs/research/`](research/).
- **Gate**: No write operations performed. Complete read-only descriptor documentation.

---

## Phase 2: Traffic Capture & Protocol Analysis
Analyze legitimate device communication through clean-room packet captures.

- [ ] Capture USB/HID traffic during official configuration interactions (e.g., using Wireshark/USBPcap on test benches).
- [ ] Isolate and document report structures:
  - Device status & battery reports
  - Lighting / RGB configuration packets
  - Rumble / haptic motor control packets
  - Deadzone and calibration parameters
  - Profile and button mapping payloads
- [ ] Document all observed fields with classification tags (`VERIFIED`, `EXPERIMENTAL`, `UNKNOWN`, `UNSUPPORTED`).
- **Gate**: Findings peer-reviewed and verified against multiple captures before writing driver logic.

---

## Phase 3: Core Protocol Engine & Mock Testing
Build the core protocol engine in [`core/`](../core/) based on verified findings.

- [ ] Implement transport abstraction layer (USB HID / OS-level transport).
- [ ] Implement type-safe packet encoders and decoders.
- [ ] Integrate safety validation layer: bounds checking, report ID validation, payload rejection for unverified fields.
- [ ] Implement mock transport and unit test suite in [`tests/`](../tests/) to replay packet captures without physical hardware.
- **Gate**: 100% test coverage of protocol packet serialization/deserialization against recorded golden captures.

---

## Phase 4: CLI & Diagnostic Tooling
Provide scriptable, lightweight command-line interfaces for power users.

- [ ] Read device status (connection mode, battery level, active profile).
- [ ] Apply verified configuration settings (lighting modes, vibration intensity, profile switching).
- [ ] Configuration persistence (local configuration files).
- **Gate**: Safe runtime verification on real physical hardware with zero persistent corruption or adverse side effects.

---

## Phase 5: Application / UI Layer
Deliver an intuitive, lightweight desktop application in [`app/`](../app/).

- [ ] Select lightweight, cross-platform UI framework (zero heavy bloat).
- [ ] Implement visual controller status monitor and profile editor.
- [ ] Optional background tray service for dynamic profile management.

---

## Phase 6: Multi-Device Extensibility
Generalize device abstractions to support additional peripherals beyond the Kreo Mirage.

- [ ] Refactor device driver interfaces into a generalized hardware abstraction layer (HAL).
- [ ] Add community driver contribution guidelines for third-party gamepads and accessories.
