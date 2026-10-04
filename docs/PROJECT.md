# COWL — Project Specification

> **“Hardware, under your command.”**

COWL is an independent, open-source hardware-control platform engineered to provide lightweight, transparent, and local-first control of gaming peripherals, initially targeting the **Kreo Mirage** controller.

---

## 1. Problem Statement & Motivation

Modern gaming hardware frequently ships with proprietary companion suites that impose significant user friction:
- Heavy system footprints and background services consuming CPU and memory.
- Platform lock-in (predominantly Windows-only support, leaving Linux and macOS users unsupported).
- Unnecessary requirements for user accounts, cloud synchronization, and telemetry.
- Inflexible configuration interfaces lacking scriptability, automation, or CLI access.

Peripherals belong to their owners. COWL restores sovereignty by providing a fast, native, local-first utility to configure and manage device capabilities without proprietary baggage.

---

## 2. Core Objectives

1. **Independent Hardware Control**: Provide full local control over device configuration features (e.g., lighting, vibration/rumble, deadzones, battery status) without depending on official vendor suites.
2. **Initial Target: Kreo Mirage Controller**: Prioritize discovering, documenting, and implementing support for the Kreo Mirage controller across supported connection interfaces (USB wired, 2.4GHz wireless dongle, and Bluetooth where applicable).
3. **Safety by Construction**: Ensure all hardware communication is bounded, schema-validated, and verified against real packet captures to prevent hardware lockup or misconfiguration.
4. **Cross-Platform Foundation**: Architect the core protocol logic to be completely decoupled from OS-specific drivers, allowing portable use across Linux, Windows, and macOS.
5. **Clean & Extensible Design**: While starting with the Kreo Mirage, design the core abstractions so additional controllers and peripherals can be integrated cleanly in the future.

---

## 3. Non-Goals

To maintain focus and safety, COWL explicitly excludes:
- **Firmware Flashing**: Modifying, flashing, or patching firmware and bootloaders is out of scope.
- **Cheating & Anti-Cheat Evasion**: COWL does not provide macros, rapid-fire scripts, or tools designed to bypass game anti-cheat systems.
- **DRM & Cryptographic Bypass**: COWL does not bypass platform authentication chips or proprietary console handshake keys.
- **Cloud Dependency**: COWL will never require accounts, internet access, telemetry, or remote servers.

---

## 4. Guiding Values

- **Local-First**: Runs offline, stores settings locally, respects user privacy.
- **Empirical**: Protocol implementation strictly driven by recorded evidence, never guesswork.
- **Minimalist**: Boring, clean, and efficient code with minimal dependencies.
