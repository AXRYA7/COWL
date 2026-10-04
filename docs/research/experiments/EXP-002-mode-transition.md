# EXP-002: Physical Mode Transition Observation

**Experiment ID:** `EXP-002`  
**Date:** `2026-10-04T14:08:25`  
**Target Hardware:** Kreo Mirage Controller  
**Safety Protocol:** Strictly Read-Only (`dwDesiredAccess = 0` / Zero HID Output or Feature Report Writes / Zero Control Transfers)  
**Methodology:** Passive Windows Plug and Play device enumeration and Win32 HID descriptor observation before and after manual mode-switch button actuation.

---

## 1. Executive Summary

During manual actuation of the physical mode-switch button combination on the Kreo Mirage controller, a complete USB bus detachment and re-enumeration was observed on `Port_#0001.Hub_#0001`:

- **Initial State (State #1):** The controller enumerated as an **Xbox 360 Controller for Windows** (`0x045E:0x028E`, `REV_0572`), handled by the Windows kernel XInput driver (`xusb22.sys`).
- **Transition Event:** Physical disconnection from the USB bus (`DEVICE_REMOVAL`) followed by re-attachment (`DEVICE_ARRIVAL`) on the exact same physical port.
- **Resulting State (State #2):** The controller re-enumerated as a **Sony DualShock 4 / PS4 Wireless Controller** (`0x054C:0x05C4`, `REV_0100`), handled as a USB Composite Device (`usbccgp.sys`) with an active audio interface and standard HID game controller interface.

```mermaid
stateDiagram-v2
    direction LR
    state "State #1 (XInput Mode)" as S1 {
        VID: 0x045E
        PID: 0x028E
        Rev: REV_0572
        Reports: In 15B / Out 0B / Feat 0B
        Driver: xusb22.sys
    }
    
    state "State #2 (DualShock 4 Mode)" as S2 {
        VID: 0x054C
        PID: 0x05C4
        Rev: REV_0100
        Reports: In 64B / Out 32B / Feat 64B
        Driver: usbccgp.sys (Composite)
    }

    [*] --> S1
    S1 --> S2: Physical Mode-Switch Actuation\n(Bus Disconnect & Re-enumeration)
```

---

## 2. Chronological State Log

### State #1 (Baseline): XInput Emulation Mode
- **Classification:** `VERIFIED`
- **Vendor ID (VID):** `0x045E` (Microsoft Corporation)
- **Product ID (PID):** `0x028E` (Xbox 360 Controller for Windows)
- **Revision:** `REV_0572`
- **Instance ID:** `USB\VID_045E&PID_028E\12345000`
- **Serial Number:** `12345000` (Matches ShanWan microcontroller platform)
- **Driver Service:** `xusb22` (`xusb22.sys`)
- **Bus Location:** `Port_#0001.Hub_#0001`
- **Friendly Name:** `Xbox 360 Controller for Windows`
- **Product String:** `Controller (Xbox 360 Controller for Windows)`
- **Manufacturer String:** `None`

#### HID Descriptor & Capabilities (State #1):
- **Input Report Length:** `15 bytes`
- **Output Report Length:** `0 bytes` (Output handled via `xusb22` driver ioctls, not exposed over HID)
- **Feature Report Length:** `0 bytes`
- **Input Buttons:** 10 digital buttons (Buttons 1–10: A, B, X, Y, LB, RB, Back, Start, L3, R3)
- **Input Values (Axes):** 6 controls:
  - `X Axis` (`0x0030`): 16-bit
  - `Y Axis` (`0x0031`): 16-bit
  - `Z Axis` (`0x0032`): 16-bit (Analog Triggers LT/RT)
  - `Rx Axis` (`0x0033`): 16-bit
  - `Ry Axis` (`0x0034`): 16-bit
  - `Hat Switch` (`0x0039`): 4-bit (1–8)

---

### Transition Event
- **Observed Sequence:** `DEVICE_REMOVAL` -> USB Bus Detach -> `DEVICE_ARRIVAL` -> PnP Re-enumeration
- **Port Continuity:** Exact same root hub port (`Port_#0001.Hub_#0001`) confirmed via Windows Device Manager location path.
- **Physical Trigger:** Manual physical mode-switch button combination on controller hardware.

---

### State #2: Sony DualShock 4 Emulation Mode
- **Classification:** `VERIFIED`
- **Vendor ID (VID):** `0x054C` (Sony Interactive Entertainment)
- **Product ID (PID):** `0x05C4` (DualShock 4 / PS4 Controller)
- **Revision:** `REV_0100`
- **Instance ID:** `USB\VID_054C&PID_05C4\6&18665E09&0&1`
- **Driver Service:** `usbccgp` (`usbccgp.sys` — USB Common Class Generic Parent)
- **Bus Location:** `Port_#0001.Hub_#0001`
- **Product String:** `Wireless Controller`
- **Manufacturer String:** `Sony Interactive Entertainment`
- **Serial Number:** `None`

#### Composite Interfaces Exposed (State #2):
1. **`MI_00` (Audio):** `USB\VID_054C&PID_05C4&MI_00\7&1EFB038D&0&0000` (`Wireless Controller` audio endpoint)
2. **`MI_03` (HID Gamepad):** `USB\VID_054C&PID_05C4&MI_03\7&1EFB038D&0&0003` -> `HID\VID_054C&PID_05C4&MI_03\8&378F3AB6&0&0000`

#### HID Descriptor & Capabilities (State #2, Interface MI_03):
- **Input Report Length:** `64 bytes`
- **Output Report Length:** `32 bytes` (Standard DS4 Output Report for RGB Lightbar & Rumble Motors!)
- **Feature Report Length:** `64 bytes` (Standard DS4 Feature Report for Calibration & Device Info!)
- **Input Buttons:** 14 digital buttons (Buttons 1–14: Square, Cross, Circle, Triangle, L1, R1, L2, R2, Share, Options, L3, R3, PS Button, Touchpad Click)
- **Input Values (Axes & Sensors):** 9 controls:
  - `X Axis` (`0x0030`): 8-bit (0–255)
  - `Y Axis` (`0x0031`): 8-bit (0–255)
  - `Z Axis` (`0x0032`): 8-bit (0–255)
  - `Rx Axis` (`0x0033`): 8-bit (0–255)
  - `Ry Axis` (`0x0034`): 8-bit (0–255)
  - `Rz Axis` (`0x0035`): 8-bit (0–255)
  - `Hat Switch` (`0x0039`): 4-bit (0–7)
  - `Generic Control` (`0x0020`): 6-bit
  - `Generic Control` (`0x0021`): 8-bit

---

## 3. Side-by-Side Mode Comparison

| Feature / Metric | State #1 (Baseline) | State #2 (Post-Transition) | Delta / Shift |
| :--- | :--- | :--- | :--- |
| **Vendor ID (VID)** | `0x045E` (Microsoft) | `0x054C` (Sony) | Mode Shift |
| **Product ID (PID)** | `0x028E` (Xbox 360) | `0x05C4` (DualShock 4) | Mode Shift |
| **Revision** | `REV_0572` | `REV_0100` | Descriptor change |
| **USB Class** | `XnaComposite` (`xusb22`) | `USB Composite` (`usbccgp`) | Driver architecture change |
| **Product String** | `Controller (Xbox 360...)` | `Wireless Controller` | Descriptor change |
| **Manufacturer** | `None` | `Sony Interactive Entertainment`| Descriptor change |
| **Input Report Size** | `15 bytes` | `64 bytes` | +49 bytes (includes gyro/accel & touchpad data) |
| **Output Report Size**| `0 bytes` | `32 bytes` | **Exposed** (RGB LED / Haptics target) |
| **Feature Report Size**| `0 bytes` | `64 bytes` | **Exposed** (Configuration target) |
| **Button Count** | 10 buttons | 14 buttons | +4 buttons |
| **Axis / Value Count**| 6 controls | 9 controls | +3 controls |

---

## 4. Key Findings & Implications for COWL

1. **Accessibility of Configuration Reports:**
   - In State #1 (`045E:028E`), Windows blocks standard user-space HID output/feature reports through the `xusb22` driver stack.
   - In State #2 (`054C:05C4`), the controller uses generic `usbccgp.sys` and standard `hidusb.sys`, exposing a **32-byte Output Report** and a **64-byte Feature Report**.
2. **Hardware Platform Confirmation:**
   - The Kreo Mirage uses a multi-emulation microcontroller platform (derived from the ShanWan codebase), capable of presenting distinct USB device descriptors depending on mode.
3. **Control Vector for Lighting & Haptics:**
   - Because standard DS4 output reports (32 bytes) carry RGB lightbar color bytes (`Red`, `Green`, `Blue`) and rumble motor speeds (`small_motor`, `large_motor`), State #2 may serve as a primary clean-room target for hardware control without proprietary vendor drivers.

---

## 5. Classification of Evidence

- **`VERIFIED`**:
  - State #1 VID/PID `0x045E:0x028E`, `REV_0572`, 15-byte input reports.
  - State #2 VID/PID `0x054C:0x05C4`, `REV_0100`, 64-byte input reports, 32-byte output reports, 64-byte feature reports.
  - Complete detachment and re-enumeration on physical port `Port_#0001.Hub_#0001`.
- **`UNKNOWN`**:
  - The exact MCU firmware registers or EEPROM addresses modified during the physical button press.
  - Whether additional physical modes exist (e.g. Switch Pro mode `057E:2009` or DirectInput mode `2563:0575`).
- **`EXPERIMENTAL`**:
  - Physical button combination sequence mapped to State #2.
- **`UNSUPPORTED`**:
  - Programmatic mode switching via software commands (strictly prohibited; clean-room read-only observation maintained).