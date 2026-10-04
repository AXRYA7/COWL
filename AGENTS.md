# AGENTS.md — Directives & Safety Guardrails for COWL

This document establishes the mandatory operational rules for AI agents and human contributors working within the COWL repository. All development must strictly adhere to the following principles.

---

## 1. Core Principles & Non-Negotiable Directives

### 1.1 Evidence Before Implementation
- Do **not** write protocol parsing code, packet decoders, or state transitions without empirical, reproducible traffic evidence documented in [`docs/research/`](docs/research/).
- Every byte offset, report ID, opcode, and checksum algorithm implemented in code must cite a specific capture or documented finding.

### 1.2 Never Invent HID Protocols or Commands
- Guessing, speculating, or hallucinating HID packets, report structures, or device commands is strictly forbidden.
- If a packet structure or parameter range is unknown, it must be marked as `UNKNOWN` and investigated through safe observation, not assumed.

### 1.3 No Arbitrary HID Writes During Research
- Blind fuzzing, random byte sending, or exploratory writes over USB/HID endpoints during research are prohibited.
- Unverified writes risk EEPROM corruption, miscalibration, or permanently bricking the target device.
- All initial device exploration must be strictly **read-only** (e.g., standard USB descriptor queries, standard HID report descriptor inspection).
- Output writes may only be attempted after a command packet has been observed, isolated, and documented from legitimate traffic captures.

### 1.4 No Firmware Modification or Flashing
- COWL is a peripheral configuration and control utility.
- Flashing, patching, dumping, or modifying device firmware or bootloaders is strictly out of scope and prohibited.

### 1.5 No DRM, Authentication, Licensing, or Security Bypass
- COWL must never implement mechanisms designed to bypass hardware DRM, cryptographic authentication, licensing restrictions, or anti-cheat boundaries.
- No features designed to automate inputs for unfair advantage or circumvent game anti-cheat systems will be accepted.

### 1.6 No Proprietary Assets or Source Code
- Do not copy, disassemble, decompile, or distribute proprietary Kreo binaries, firmware blobs, official software source code, icons, or assets.
- Research must follow clean-room methodology: reverse engineering through standard bus monitoring (e.g., Wireshark/USBPcap) and protocol specification analysis.

### 1.7 Independent and Unofficial Identity
- COWL is an independent open-source project.
- Always maintain clear separation from Kreo. Do not use official logos, trademarked styling, or claim endorsement, partnership, or official status.

---

## 2. Research Findings Classification

Every finding, report structure, command ID, or byte definition in documentation or code comments must be categorized using one of these four tags:

| Status Tag | Definition | Permitted Usage |
| :--- | :--- | :--- |
| **`VERIFIED`** | Confirmed through repeated bidirectional bus captures and tested without unintended side effects. | Ready for production implementation in `core/`. |
| **`EXPERIMENTAL`** | Observed in traffic captures or tested under limited conditions; structure is partially understood but edge cases remain unverified. | Permitted only behind explicit flags/development tooling. |
| **`UNKNOWN`** | Field, byte sequence, or report exists in captures but semantics or valid ranges are unconfirmed. | Document in `docs/research/`; do not execute or emit. |
| **`UNSUPPORTED`** | Functionality identified as out of scope, hazardous, protected, or requiring firmware modification. | Documented as out of scope; never implement. |

---

## 3. Engineering Workflow for Agents

1. **Investigate (Read-Only)**: Use non-destructive tools in [`tools/device-probe/`](tools/device-probe/) to enumerate endpoints and descriptors.
2. **Document**: Record all traffic captures and structural findings in [`docs/research/`](docs/research/) with full provenance and classification tags.
3. **Design**: Document significant architectural or protocol decisions in [`docs/decisions/`](docs/decisions/) before writing code.
4. **Implement Minimally**: Implement only verified protocol segments in [`core/`](core/). Write unit tests in [`tests/`](tests/) with mock fixtures before real-device testing.
5. **Keep It Lean**: Follow minimal engineering—shortest working diff, zero speculative abstractions, minimal external dependencies.
