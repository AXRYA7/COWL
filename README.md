# COWL

> “Hardware, under your command.”

COWL is an independent, open-source, unofficial hardware-control platform initially targeting the Kreo Mirage controller.

---

## Notice & Disclaimer

COWL is an independent open-source project and is **not** affiliated with, endorsed by, or associated with Kreo or any of its parent companies, subsidiaries, or affiliates. All product names, logos, brands, and registered trademarks mentioned are the property of their respective owners.

This project is developed strictly through clean-room observation and standard protocol analysis to provide local, privacy-focused peripheral configuration.

---

## Status

**Phase 0: Repository Foundation & Research Setup**

- [x] Initial repository structure and safety guardrails established
- [ ] Read-only device probing and descriptor analysis
- [ ] Safe USB/HID traffic observation and protocol documentation
- [ ] Protocol engine implementation
- [ ] User application / interface

*Hardware commands and frontend interfaces are deliberately not implemented at this stage. See [docs/ROADMAP.md](docs/ROADMAP.md) for current progress.*

---

## Safety Principles

Hardware safety is the highest priority:
1. **Evidence Before Implementation**: No protocol code is merged without verified, reproducible traffic captures.
2. **Zero Speculative Writes**: Blind fuzzing and arbitrary HID writes are strictly prohibited to prevent device corruption or bricking.
3. **No Firmware Modification**: COWL operates exclusively within the controller's runtime configuration interfaces; it will never flash or alter device firmware.
4. **Clean-Room & Legal Compliance**: No proprietary binaries, decompiled source code, or vendor assets are included or distributed.

---

## Repository Structure

```text
COWL/
├── app/                  # Application layer (CLI / desktop interface)
├── core/                 # Protocol engine, device abstraction, and safety guards
├── docs/
│   ├── PROJECT.md        # Mission, scope, and objectives
│   ├── ROADMAP.md        # Development phases and milestones
│   ├── ARCHITECTURE.md   # System design and component boundaries
│   ├── research/         # Observed HID captures and protocol documentation
│   └── decisions/        # Architecture Decision Records (ADRs)
├── tests/                # Unit tests and mock protocol fixtures
├── tools/
│   └── device-probe/     # Safe, read-only hardware inspection utilities
├── AGENTS.md             # Directives and constraints for AI agents & contributors
├── CONTRIBUTING.md       # Contribution guidelines and research protocol
├── LICENSE               # Apache-2.0 License
├── README.md             # Project overview (this file)
└── SECURITY.md           # Security and hardware safety policy
```

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).
