# EXP-004: Official Software & Legitimate Traffic Investigation

**Status:** Completed  
**Date:** 2026-10-04  
**Author:** COWL Research & Hardware Security Team  
**Scope:** Official Kreo Software Ecosystem & Kreo Mirage Controller  
**Classification:** `VERIFIED` / `EXPERIMENTAL` / `UNKNOWN` / `UNSUPPORTED` (tagged per finding)

---

## 1. Objective

Investigate whether official Kreo Windows software exists for the Kreo Mirage controller, determine whether it communicates with the device over USB/HID, and evaluate whether any legitimate software-driven mechanism for switching controller modes is exposed or utilized.

---

## 2. Investigation Methodology & Evidence Gathering

### 2.1 Audit of Kreo Kontrol (`kontrol.kreo-tech.com`)
Kreo provides a modern browser-based configuration hub, **Kreo Kontrol**, utilizing the WebHID API in Chromium browsers. We conducted a clean-room static analysis of all client-side JavaScript bundles deployed to production:
- **Analyzed Bundles:**
  - `index-CIXBs9J0.js`
  - `driver-core-sf7XGx09.js`
  - `app-state-B409OPvv.js`
  - `auth-pages-DGDmHapL.js`
  - `vendor-router-DvzQETdX.js`
- **Findings:**
  - **Device Registry:** The driver core (`driver-core-sf7XGx09.js`) defines support exclusively for Keyboards (`Swarm 65`, `Swarm 75/X`, `Hive 65`, `Hive 75 HE`, `Hive 98 V2`) and Mice (`Ikarus`, `Anzu`, `Chimera V2`, `Harpy`, `Hawk`).
  - **Controller Support:** Exact match search for `mirage`, `Mirage`, `gamepad`, `controller`, `045e`, `054c`, `028e`, `05c4` revealed **0 device models, 0 VID/PID filters, and 0 HID handler routines** for game controllers [`VERIFIED`].
  - **Conclusion on Kreo Kontrol:** Kreo Kontrol does not support, recognize, or communicate with the Kreo Mirage controller [`VERIFIED`].

### 2.2 Audit of Official Kreo Downloads & Support Documentation
- **Product Manual & FAQs:**
  - Official product literature confirms that the Kreo Mirage operates as a **driverless, plug-and-play peripheral** [`VERIFIED`].
  - Hardware functions—including Macro programming (back buttons M1/M2), vibration intensity adjustment, and RGB lighting presets—are handled **entirely onboard the controller hardware** via physical button chords, rather than through software [`VERIFIED`].
  - Official documentation explicitly recommends using the controller in wired XInput mode for native Windows compatibility and advises using third-party tools (such as **DS4Windows**) if users wish to map the touchpad or configure custom PC mappings in PlayStation mode [`VERIFIED`].
- **Firmware Update Tool:**
  - A firmware flasher utility exists but requires booting the controller into an offline DFU/bootloader mode (`Share + X` held during USB insertion) [`VERIFIED`].
  - Per [AGENTS.md §1.4](file:///d:/COWL/COWL/AGENTS.md), firmware modification, dumping, and bootloader flashing are strictly out of scope for COWL.

---

## 3. Findings & Protocol Analysis

| Question / Parameter | Empirical Finding | Classification |
| :--- | :--- | :--- |
| **Does official Mirage configuration software exist?** | **No.** Kreo does not distribute an official Windows companion or configuration utility for the Mirage. | `VERIFIED` |
| **Does Kreo Kontrol communicate with the Mirage?** | **No.** Static audit of the production WebHID bundles confirms 0 controller device entries or VID/PID bindings. | `VERIFIED` |
| **Are proprietary HID/USB protocols used on Windows?** | **No.** The device presents standard Microsoft XInput (`045E:028E`) or standard Sony DualShock 4 (`054C:05C4`) emulation. | `VERIFIED` |
| **Is there an official software mode-switch mechanism?** | **No.** Mode switching is executed strictly via hardware button inputs on the controller itself. | `UNSUPPORTED` (via software) |

---

## 4. USB Interface Observation Summary

Because no official companion software runs on the host during normal controller operation:

### 4.1 State 1 (XInput Mode — `045E:028E`)
- Windows assigns Microsoft's in-box driver `xusb22.sys`.
- Exposes no user-space HID Feature or Output endpoints (`OutputReportByteLength = 0`, `FeatureReportByteLength = 0`).
- No vendor-specific HID interfaces are exposed to user space.

### 4.2 State 2 (DualShock 4 Mode — `054C:05C4`)
- Windows assigns standard `usbccgp.sys` (composite parent), `usbaudio.sys` (`MI_00` / `MI_01` / `MI_02`), and `HidUsb.sys` (`MI_03`).
- `MI_03` presents standard DualShock 4 HID report descriptors (64-byte Input, 32-byte Output, 64-byte Feature).
- Any host software interacting with this mode (e.g., Steam Input, DS4Windows) speaks standard Sony DS4 HID reports, not a proprietary Kreo protocol.

---

## 5. Safety & Guardrail Compliance

1. **No Speculative Packet Injection ([AGENTS.md §1.2, §1.3](file:///d:/COWL/COWL/AGENTS.md)):**
   - No guessed HID feature packets or synthetic EP0 control transfers were transmitted.
2. **No Firmware Flashing or Bootloader Tampering ([AGENTS.md §1.4](file:///d:/COWL/COWL/AGENTS.md)):**
   - The bootloader update mode (`Share + X`) was identified but intentionally excluded from operational analysis to prevent EEPROM/flash risks.
3. **No Proprietary Decompilation ([AGENTS.md §1.6](file:///d:/COWL/COWL/AGENTS.md)):**
   - Analysis relied solely on publicly accessible web assets and official documentation.

---

## 6. Conclusions

1. **Absence of Proprietary Host Software:**
   - The Kreo Mirage is an autonomous, firmware-driven multi-mode peripheral with no proprietary Windows host software companion.
   - All customizations (RGB modes, vibration intensity, macro assignments, and mode switching) are implemented on-chip by the controller MCU.
2. **Standard Emulation Architecture:**
   - Rather than implementing a custom vendor HID protocol, the Mirage relies on standards-based platform emulation:
     - PC/Xbox mode: Genuine Xbox 360 controller emulation (`045E:028E`) handled by `xusb22.sys`.
     - PS4 mode: Genuine DualShock 4 emulation (`054C:05C4`) handled by `HidUsb.sys` and standard DS4 drivers.
3. **Engineering Implications for COWL:**
   - COWL does not need to reverse engineer a proprietary Kreo Windows driver or vendor communication protocol.
   - COWL can interface directly with the controller using:
     - In State 1 (`045E:028E`): Standard Windows XInput API / RawInput for high-performance input reads.
     - In State 2 (`054C:05C4`): Standard DualShock 4 HID protocol over `HidUsb` for full access to touchpad, motion sensors (gyro/accelerometer), RGB lightbar, and dual rumble motors.

---

## 7. Recommended Next Experiment (EXP-005)

- **EXP-005: DualShock 4 Emulation Fidelity & Input Report Mapping**
  - **Objective:** Verify the structure and accuracy of the 64-byte HID Input report emitted by `054C:05C4` (MI_03) in read-only mode.
  - **Test Plan:**
    1. Read input reports from `MI_03` using non-exclusive Win32 HID read handles.
    2. Map button bits, analog sticks (LX, LY, RX, RY), analog triggers (L2, R2), IMU / motion sensor data, and capacitive touchpad coordinates.
    3. Verify whether report format strictly matches the Sony DualShock 4 USB specification (Report ID 0x01).
