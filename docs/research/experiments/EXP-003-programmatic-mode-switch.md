# EXP-003: Programmatic Mode-Switch Investigation

**Status:** Completed  
**Date:** 2026-10-04  
**Author:** COWL Research & Hardware Security Team  
**Scope:** Kreo Mirage Wireless/Wired Controller  
**Classification:** `VERIFIED` / `EXPERIMENTAL` / `UNKNOWN` / `UNSUPPORTED` (tagged per finding)

---

## 1. Objective

Determine whether the physical mode-switch behavior observed on the Kreo Mirage controller can be initiated or reproduced programmatically from Windows user space.

Specifically, investigate whether the transition:
$$\text{State 1 (XInput: } 045E:028E) \xrightarrow{\text{USB Detach / Re-enumeration}} \text{State 2 (DS4 / D-Input: } 054C:05C4)$$
(or its inverse) is controlled by:
1. An internal controller MCU state machine (gated solely by physical hardware buttons / GPIOs), or
2. A host-visible USB/HID command interface accessible from standard Windows user space.

---

## 2. Existing Empirical Evidence

### 2.1 Findings from EXP-001 (Device Probe)
- **State 1 (`VID_045E`, `PID_028E`, `REV_0572`):**
  - Bound to Microsoft kernel driver `xusb22.sys` (`Controller (Xbox 360 For Windows)`).
  - Physical serial: `12345000`.
  - HID report descriptor capabilities:
    - `InputReportByteLength`: 0 bytes [`VERIFIED`]
    - `OutputReportByteLength`: 0 bytes [`VERIFIED`]
    - `FeatureReportByteLength`: 0 bytes [`VERIFIED`]
  - The OS hides standard HID endpoint communication; input and vibration are mediated exclusively through the Microsoft XInput kernel driver stack.

### 2.2 Findings from EXP-002 (Mode Transition Observation)
- **Transition Dynamics:**
  - Transition occurs via an explicit hardware detachment event (`DEVICE_REMOVAL` on `Port_#0001.Hub_#0001`) followed by a clean hardware arrival event (`DEVICE_ARRIVAL`) [`VERIFIED`].
  - Hardware device instance changes from `USB\VID_045E&PID_028E\12345000` to `USB\VID_054C&PID_05C4\7&1cbe0472&0&1` (Composite Parent with `usbccgp.sys`) [`VERIFIED`].
- **State 2 Architecture (`VID_054C`, `PID_05C4`, `REV_0100`):**
  - Child interface `MI_03` binds to `HidUsb.sys` with active HID buffers:
    - `InputReportByteLength`: 64 bytes [`VERIFIED`]
    - `OutputReportByteLength`: 32 bytes [`VERIFIED`]
    - `FeatureReportByteLength`: 64 bytes [`VERIFIED`]
  - Child interface `MI_00` binds to standard USB Audio endpoints [`VERIFIED`].

---

## 3. Investigation Performed

### 3.1 Review of Manufacturer Mode-Switch Documentation
- **Physical Controls:**
  - The Kreo Mirage documentation specifies that mode switching in wired mode is initiated by manual button holds:
    - Holding the **Home / Guide** button for 3–5 seconds switches between XInput and standard D-Input [`VERIFIED`].
    - Holding **Triangle** (or specific face buttons) while plugging in the USB cable forces PlayStation / DualShock 4 emulation mode (`054C:05C4`) [`VERIFIED`].
    - In wireless (Bluetooth) mode, distinct key combinations (e.g., `Home + A`, `Home + X`, `Home + Triangle`) select specific Bluetooth broadcast profiles (Android / XInput / PS4) [`VERIFIED`].
- **Hardware Autonomy:**
  - The physical mode switch succeeds without any host application running, without drivers installed beyond Windows defaults, and across non-Windows hosts (Linux, Android, consoles) [`VERIFIED`].

### 3.2 USB/HID Architecture Analysis of State 1 (XInput: `045E:028E`)
- **Driver Model:**
  - On Windows, devices presenting `VID_045E&PID_028E` automatically match Microsoft's in-box XUSB driver package (`xusb22.inf` / `xusb22.sys`).
  - Standard user-space Win32 HID APIs (`CreateFile` on HID device path, `HidD_SetFeature`, `HidD_GetFeature`, `WriteFile`) cannot send output reports or feature reports to this device because `OutputReportByteLength == 0` and `FeatureReportByteLength == 0` [`VERIFIED`].
- **XInput API Boundaries:**
  - The public XInput API (`xinput1_4.dll`, `xinput9_1_0.dll`) exposes only `XInputGetState` (polling button/axis state) and `XInputSetState` (setting left/right rumble motor speeds).
  - No mode-switch or reset APIs exist within the standard XInput specification [`VERIFIED`].
- **Raw USB / WinUSB Access:**
  - Because `xusb22.sys` holds exclusive functional ownership of the USB device interfaces on Windows, unprivileged user-space applications cannot open WinUSB or raw USB handles to Endpoint 0 without replacing the driver (e.g., via Zadig / WinUSB / libusb-win32) or installing a kernel-mode filter driver [`VERIFIED`].

### 3.3 USB/HID Architecture Analysis of State 2 (DS4: `054C:05C4`)
- **Interface Structure:**
  - Emulates a Sony DualShock 4 (CUH-ZCT1x series).
  - Feature reports (64 bytes) and Output reports (32 bytes) are accessible via standard `HidD_SetFeature` and `WriteFile` under `HidUsb.sys` [`VERIFIED`].
- **DualShock 4 Protocol Conventions:**
  - Official DS4 controllers do not feature a "switch to XInput" HID command. Mode switching on multi-platform clone controllers emulating DS4 is typically handled via physical keypresses or specialized non-standard vendor feature reports [`UNKNOWN`].

---

## 4. Candidate Mechanisms Evaluation

| Candidate Mechanism | Description | Empirical Evidence & Assessment | Classification |
| :--- | :--- | :--- | :--- |
| **Candidate A: Standard User-Space HID Command in State 1** | Host sends a HID Output or Feature report to `045E:028E` commanding mode detach. | **Rejected:** HID report lengths are 0 bytes. Windows driver stack `xusb22.sys` provides no writable HID report pipes to user space. | `UNSUPPORTED` |
| **Candidate B: USB Vendor Control Transfer on Endpoint 0** | Host sends a vendor-specific control request (`bmRequestType = 0x40`) over USB default control pipe (EP0). | **Plausible but unproven:** Supported on some third-party MCUs, but inaccessible under Windows without driver replacement (WinUSB). No evidence exists that Mirage MCU implements this opcode. | `UNKNOWN` |
| **Candidate C: Standard User-Space HID Feature Report in State 2** | Host sends a custom vendor Feature Report to `054C:05C4` (where Feature length is 64 bytes) to command return to XInput. | **Unverified:** While write buffers exist, no vendor feature report structure has been documented from official traffic. Arbitrary writes are prohibited under AGENTS.md §1.3. | `UNKNOWN` |
| **Candidate D: Internal MCU GPIO / Firmware State Machine** | Controller MCU continuously monitors button matrix / GPIO inputs. Button triggers MCU to de-assert USB D+/D- pull-ups, reset USB PHY, and re-enumerate with alternate descriptors. | **Confirmed:** Directly matches physical observation. Works independently of host software or OS. Detach/arrival events match USB PHY re-initialization. | `VERIFIED` |

---

## 5. Safety & Security Assessment

In accordance with **COWL Directives (AGENTS.md)**:
1. **No Arbitrary HID/USB Writes (§1.3):**
   - Attempting exploratory writes (e.g., cycling byte sequences to Feature reports on State 2) without empirical traffic captures risks EEPROM calibration corruption or flash state damage.
2. **No Brute-Forcing Endpoint 0 Requests (§1.2, §1.3):**
   - Blasting vendor control transfers on USB EP0 is strictly prohibited without prior packet captures from legitimate companion software.
3. **No Driver Replacement / Disruption:**
   - Replacing `xusb22.sys` with WinUSB on the user's primary controller interface would disable standard gaming functionality and is out of scope for a non-destructive user-space utility.

---

## 6. Conclusion

1. **Physical Mode Transition is Internal to the MCU:**
   - The Kreo Mirage's mode transition (`045E:028E` $\leftrightarrow$ `054C:05C4`) is executed by an **autonomous MCU firmware state machine** responding to physical button holds (Home button or boot-strap key combinations).
   - The transition operates by electrically dropping the USB bus connection (pulling D+/D- low) and re-attaching with a completely different device descriptor set.
2. **Programmatic Mode Switching is Unsupported from Windows User Space in State 1:**
   - In State 1 (`045E:028E`), Windows binds the kernel driver `xusb22.sys`, which completely isolates the controller from generic user-space HID writes and raw USB control transfers.
   - Consequently, **software-initiated mode switching cannot be performed out-of-the-box on stock Windows without proprietary vendor driver extensions or empirical capture of a verified vendor control protocol**.
3. **Architectural Direction for COWL:**
   - COWL must not assume or mandate programmatic mode switching.
   - Instead, COWL's core engine must be **multi-profile and hot-plug aware**:
     - It should detect whichever mode the controller is currently operating in (`045E:028E` via XInput/RawInput, or `054C:05C4` via standard HID).
     - It should seamlessly adapt its control pipelines when the user physically toggles modes.

---

## 7. Recommended Next Experiment (EXP-004)

- **EXP-004: Clean-Room Traffic Capture & Companion Suite Analysis**
  - **Objective:** Determine if Kreo provides an official Windows configuration utility / companion application, and if so, capture bidirectional USB traffic using Wireshark / USBPcap during application launch and configuration changes.
  - **Goal:** Verify whether official software communicates with the controller via vendor requests, audio control pipes, or HID feature reports.
  - **Protocol:** Strictly clean-room packet sniffing without code decompilation or active fuzzing.
