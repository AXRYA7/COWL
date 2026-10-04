# Contributing to COWL

Thank you for your interest in contributing to COWL (“Hardware, under your command”).

COWL is an open-source, community-driven project aiming to provide transparent, lightweight, and safe peripheral control. Because we interact directly with hardware, contributions must follow strict safety, legal, and engineering standards.

---

## 1. Guiding Principles

- **Hardware Safety First**: Hardware cannot be easily repaired if misconfigured or bricked. We never take risks with exploratory writes or unverified payloads.
- **Clean-Room Engineering**: All protocol specifications must be derived from clean observation (e.g., standard USB captures using Wireshark/USBPcap) and non-destructive inspection. Never inspect, decompile, or commit proprietary binaries or vendor source code.
- **Minimal, Auditable Code**: Write the simplest code that solves the problem. Avoid premature abstractions, speculative features, or heavy dependencies.
- **Independent & Unofficial**: COWL has no connection to Kreo. Never use official branding or claim official status.

---

## 2. Research & Findings Process

Before any code implementing hardware communication is accepted:
1. **Submit Evidence**: Document the observed packets in [`docs/research/`](docs/research/). Include packet hex dumps, report IDs, direction (Host-to-Device / Device-to-Host), and trigger conditions.
2. **Apply Classification Tags**:
   - `VERIFIED`: Repeatedly confirmed and safe.
   - `EXPERIMENTAL`: Observed in captures but edge cases or full semantics are unverified.
   - `UNKNOWN`: Observed byte fields with unknown meaning.
   - `UNSUPPORTED`: Unsafe, out of scope, or incompatible features.
3. **Architecture Decisions**: For major design choices or protocol structure shifts, open a record in [`docs/decisions/`](docs/decisions/).

---

## 3. What We Do NOT Accept

Pull requests containing any of the following will be rejected immediately:
- Guessed or unverified HID commands/magic bytes.
- Scripts or tools performing blind fuzzing or arbitrary writes to USB/HID endpoints.
- Firmware flashing, patching, dumping, or bootloader manipulation routines.
- Decompiled code, extracted strings, or proprietary assets from official vendor software.
- Tools designed to bypass authentication, DRM, or anti-cheat safeguards.

---

## 4. Development Workflow

1. **Fork and Branch**: Create a feature branch from `main`.
2. **Implement with Mock Fixtures**: Core protocol logic in [`core/`](core/) must be covered by unit tests in [`tests/`](tests/) using byte-level mock transports rather than requiring physical hardware to run CI.
3. **Run Checks**: Ensure your code is formatted, lints cleanly, and passes existing tests.
4. **Submit PR**: Clearly state what problem the PR solves, link to relevant evidence in `docs/research/`, and keep diffs small and focused.
