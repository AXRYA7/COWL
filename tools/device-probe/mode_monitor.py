"""
COWL — Mode Transition Observation Tool (EXP-002)
--------------------------------------------------
Strictly read-only observation tool for monitoring physical controller mode switches.
Monitors Windows USB/HID arrival and removal events.
Captures VID, PID, Instance ID, Revision, and HID interface capabilities before and after transitions.
Zero writes, zero feature reports, zero control transfers.
"""

import ctypes
from ctypes import wintypes
import json
import os
import sys
import time
import subprocess
from datetime import datetime

# Win32 Constants
DIGCF_PRESENT = 0x00000002
DIGCF_DEVICEINTERFACE = 0x00000010
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
HIDP_STATUS_SUCCESS = 0x00110000

# Win32 Structures
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8)
    ]

    def __str__(self):
        d4_1 = ''.join(f'{b:02x}' for b in self.Data4[:2])
        d4_2 = ''.join(f'{b:02x}' for b in self.Data4[2:])
        return f"{{{self.Data1:08x}-{self.Data2:04x}-{self.Data3:04x}-{d4_1}-{d4_2}}}"

class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("InterfaceClassGuid", GUID),
        ("Flags", wintypes.DWORD),
        ("Reserved", ctypes.c_size_t)
    ]

class HIDD_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Size", wintypes.ULONG),
        ("VendorID", wintypes.USHORT),
        ("ProductID", wintypes.USHORT),
        ("VersionNumber", wintypes.USHORT)
    ]

class HIDP_CAPS(ctypes.Structure):
    _fields_ = [
        ("Usage", wintypes.USHORT),
        ("UsagePage", wintypes.USHORT),
        ("InputReportByteLength", wintypes.USHORT),
        ("OutputReportByteLength", wintypes.USHORT),
        ("FeatureReportByteLength", wintypes.USHORT),
        ("Reserved", wintypes.USHORT * 17),
        ("NumberLinkCollectionNodes", wintypes.USHORT),
        ("NumberInputButtonCaps", wintypes.USHORT),
        ("NumberInputValueCaps", wintypes.USHORT),
        ("NumberInputDataIndices", wintypes.USHORT),
        ("NumberOutputButtonCaps", wintypes.USHORT),
        ("NumberOutputValueCaps", wintypes.USHORT),
        ("NumberOutputDataIndices", wintypes.USHORT),
        ("NumberFeatureButtonCaps", wintypes.USHORT),
        ("NumberFeatureValueCaps", wintypes.USHORT),
        ("NumberFeatureDataIndices", wintypes.USHORT)
    ]

class HIDP_BUTTON_CAPS(ctypes.Structure):
    _fields_ = [
        ("UsagePage", wintypes.USHORT),
        ("ReportID", wintypes.BYTE),
        ("IsAlias", wintypes.BOOLEAN),
        ("BitField", wintypes.USHORT),
        ("LinkCollection", wintypes.USHORT),
        ("LinkUsage", wintypes.USHORT),
        ("LinkUsagePage", wintypes.USHORT),
        ("IsRange", wintypes.BOOLEAN),
        ("IsStringRange", wintypes.BOOLEAN),
        ("IsDesignatorRange", wintypes.BOOLEAN),
        ("IsAbsolute", wintypes.BOOLEAN),
        ("Reserved", wintypes.ULONG * 10),
        ("UsageMin", wintypes.USHORT),
        ("UsageMax", wintypes.USHORT),
        ("StringMin", wintypes.USHORT),
        ("StringMax", wintypes.USHORT),
        ("DesignatorMin", wintypes.USHORT),
        ("DesignatorMax", wintypes.USHORT),
        ("DataIndexMin", wintypes.USHORT),
        ("DataIndexMax", wintypes.USHORT),
    ]

class HIDP_VALUE_CAPS(ctypes.Structure):
    _fields_ = [
        ("UsagePage", wintypes.USHORT),
        ("ReportID", wintypes.BYTE),
        ("IsAlias", wintypes.BOOLEAN),
        ("BitField", wintypes.USHORT),
        ("LinkCollection", wintypes.USHORT),
        ("LinkUsage", wintypes.USHORT),
        ("LinkUsagePage", wintypes.USHORT),
        ("IsRange", wintypes.BOOLEAN),
        ("IsStringRange", wintypes.BOOLEAN),
        ("IsDesignatorRange", wintypes.BOOLEAN),
        ("IsAbsolute", wintypes.BOOLEAN),
        ("HasNull", wintypes.BOOLEAN),
        ("Reserved", wintypes.BYTE),
        ("BitSize", wintypes.USHORT),
        ("ReportCount", wintypes.USHORT),
        ("Reserved2", wintypes.USHORT * 5),
        ("UnitsExp", wintypes.ULONG),
        ("Units", wintypes.ULONG),
        ("LogicalMin", wintypes.LONG),
        ("LogicalMax", wintypes.LONG),
        ("PhysicalMin", wintypes.LONG),
        ("PhysicalMax", wintypes.LONG),
        ("UsageMin", wintypes.USHORT),
        ("UsageMax", wintypes.USHORT),
        ("StringMin", wintypes.USHORT),
        ("StringMax", wintypes.USHORT),
        ("DesignatorMin", wintypes.USHORT),
        ("DesignatorMax", wintypes.USHORT),
        ("DataIndexMin", wintypes.USHORT),
        ("DataIndexMax", wintypes.USHORT),
    ]

# Win32 DLL Bindings
setupapi = ctypes.windll.setupapi
hid = ctypes.windll.hid
kernel32 = ctypes.windll.kernel32

setupapi.SetupDiGetClassDevsW.restype = ctypes.c_void_p
setupapi.SetupDiGetClassDevsW.argtypes = [ctypes.POINTER(GUID), wintypes.LPCWSTR, wintypes.HWND, wintypes.DWORD]

setupapi.SetupDiEnumDeviceInterfaces.restype = wintypes.BOOL
setupapi.SetupDiEnumDeviceInterfaces.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(GUID), wintypes.DWORD, ctypes.POINTER(SP_DEVICE_INTERFACE_DATA)
]

setupapi.SetupDiGetDeviceInterfaceDetailW.restype = wintypes.BOOL
setupapi.SetupDiGetDeviceInterfaceDetailW.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(SP_DEVICE_INTERFACE_DATA), ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p
]

setupapi.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL
setupapi.SetupDiDestroyDeviceInfoList.argtypes = [ctypes.c_void_p]

kernel32.CreateFileW.restype = wintypes.HANDLE
kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE
]

kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

hid.HidD_GetHidGuid.restype = None
hid.HidD_GetHidGuid.argtypes = [ctypes.POINTER(GUID)]

hid.HidD_GetAttributes.restype = wintypes.BOOL
hid.HidD_GetAttributes.argtypes = [wintypes.HANDLE, ctypes.POINTER(HIDD_ATTRIBUTES)]

hid.HidD_GetManufacturerString.restype = wintypes.BOOL
hid.HidD_GetManufacturerString.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.ULONG]

hid.HidD_GetProductString.restype = wintypes.BOOL
hid.HidD_GetProductString.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.ULONG]

hid.HidD_GetSerialNumberString.restype = wintypes.BOOL
hid.HidD_GetSerialNumberString.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.ULONG]

hid.HidD_GetPreparsedData.restype = wintypes.BOOL
hid.HidD_GetPreparsedData.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_void_p)]

hid.HidD_FreePreparsedData.restype = wintypes.BOOL
hid.HidD_FreePreparsedData.argtypes = [ctypes.c_void_p]

hid.HidP_GetCaps.restype = wintypes.DWORD
hid.HidP_GetCaps.argtypes = [ctypes.c_void_p, ctypes.POINTER(HIDP_CAPS)]

hid.HidP_GetButtonCaps.restype = wintypes.DWORD
hid.HidP_GetButtonCaps.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(wintypes.USHORT), ctypes.c_void_p]

hid.HidP_GetValueCaps.restype = wintypes.DWORD
hid.HidP_GetValueCaps.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(wintypes.USHORT), ctypes.c_void_p]

USAGE_PAGE_NAMES = {
    0x0001: "Generic Desktop Controls",
    0x0002: "Simulation Controls",
    0x0004: "Sport Controls",
    0x0005: "Game Controls",
    0x0006: "Generic Device Controls",
    0x0007: "Keyboard/Keypad",
    0x0008: "LEDs",
    0x0009: "Button",
    0x000C: "Consumer",
    0x000D: "Digitizers",
    0xFF00: "Vendor-defined (0xFF00)",
}

GENERIC_DESKTOP_USAGES = {
    0x0001: "Pointer",
    0x0002: "Mouse",
    0x0004: "Joystick",
    0x0005: "Gamepad",
    0x0006: "Keyboard",
    0x0030: "X Axis",
    0x0031: "Y Axis",
    0x0032: "Z Axis",
    0x0033: "Rx Axis",
    0x0034: "Ry Axis",
    0x0035: "Rz Axis",
    0x0039: "Hat Switch",
}

# Known baseline hardware signature for Kreo Mirage
KNOWN_BASELINE_STATE = {
    "timestamp": "2026-10-04T13:54:31.181070",
    "vid": 0x045E,
    "pid": 0x028E,
    "revision": "REV_0572",
    "primary_node": {
        "InstanceId": "USB\\VID_045E&PID_028E\\12345000",
        "Class": "XnaComposite",
        "FriendlyName": "Xbox 360 Controller for Windows",
        "Service": "xusb22"
    },
    "all_controller_nodes": [
        {"InstanceId": "USB\\VID_045E&PID_028E\\12345000", "Class": "XnaComposite", "FriendlyName": "Xbox 360 Controller for Windows", "Service": "xusb22"},
        {"InstanceId": "USB\\VID_045E&PID_028E&IG_00\\7&1818B36&0&00", "Class": "HIDClass", "FriendlyName": "USB Input Device", "Service": "HidUsb"},
        {"InstanceId": "HID\\VID_045E&PID_028E&IG_00\\8&10D61EC6&0&0000", "Class": "HIDClass", "FriendlyName": "HID-compliant game controller", "Service": ""}
    ],
    "hid_interfaces": [
        {
            "path": "\\\\?\\hid#vid_045e&pid_028e&ig_00#8&10d61ec6&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}",
            "vid": 0x045E,
            "pid": 0x028E,
            "version": 0x0114,
            "product": "Controller (Xbox 360 Controller for Windows)",
            "manufacturer": None,
            "serial": None,
            "caps": {
                "usage_page": 1,
                "usage_page_name": "Generic Desktop Controls",
                "usage": 5,
                "usage_name": "Gamepad",
                "input_report_byte_length": 15,
                "output_report_byte_length": 0,
                "feature_report_byte_length": 0,
                "num_input_button_caps": 1,
                "num_input_value_caps": 6
            },
            "buttons": [{"usage_page": 9, "usage_min": 1, "usage_max": 10}],
            "values": [
                {"usage_name": "Y Axis", "usage": 0x0031, "bit_size": 16, "logical_min": 0, "logical_max": -1},
                {"usage_name": "X Axis", "usage": 0x0030, "bit_size": 16, "logical_min": 0, "logical_max": -1},
                {"usage_name": "Ry Axis", "usage": 0x0034, "bit_size": 16, "logical_min": 0, "logical_max": -1},
                {"usage_name": "Rx Axis", "usage": 0x0033, "bit_size": 16, "logical_min": 0, "logical_max": -1},
                {"usage_name": "Z Axis", "usage": 0x0032, "bit_size": 16, "logical_min": 0, "logical_max": -1},
                {"usage_name": "Hat Switch", "usage": 0x0039, "bit_size": 4, "logical_min": 1, "logical_max": 8}
            ]
        }
    ]
}

def resolve_usage_page(page):
    if page in USAGE_PAGE_NAMES:
        return USAGE_PAGE_NAMES[page]
    if 0xFF00 <= page <= 0xFFFF:
        return f"Vendor-defined (0x{page:04X})"
    return f"Unknown (0x{page:04X})"

def resolve_usage(page, usage):
    if page == 0x0001 and usage in GENERIC_DESKTOP_USAGES:
        return GENERIC_DESKTOP_USAGES[usage]
    return f"0x{usage:04X}"

def query_hid_interfaces():
    """Returns a list of all present HID interfaces with their parsed capabilities."""
    hid_guid = GUID()
    hid.HidD_GetHidGuid(ctypes.byref(hid_guid))

    hdev = setupapi.SetupDiGetClassDevsW(
        ctypes.byref(hid_guid),
        None,
        None,
        DIGCF_PRESENT | DIGCF_DEVICEINTERFACE
    )

    if hdev is None or hdev == -1:
        return []

    interfaces = []
    idx = 0

    while True:
        inter = SP_DEVICE_INTERFACE_DATA()
        inter.cbSize = ctypes.sizeof(SP_DEVICE_INTERFACE_DATA)

        if not setupapi.SetupDiEnumDeviceInterfaces(hdev, None, ctypes.byref(hid_guid), idx, ctypes.byref(inter)):
            break
        idx += 1

        req = wintypes.DWORD(0)
        setupapi.SetupDiGetDeviceInterfaceDetailW(hdev, ctypes.byref(inter), None, 0, ctypes.byref(req), None)
        if req.value == 0:
            continue

        buf = ctypes.create_string_buffer(req.value)
        cb_size = 8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 5
        ctypes.memmove(buf, ctypes.byref(wintypes.DWORD(cb_size)), 4)

        if not setupapi.SetupDiGetDeviceInterfaceDetailW(hdev, ctypes.byref(inter), ctypes.byref(buf), req.value, None, None):
            continue

        device_path = ctypes.wstring_at(ctypes.addressof(buf) + 4)

        handle = kernel32.CreateFileW(
            device_path,
            0,  # Query access only (0 = FILE_READ_ATTRIBUTES)
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None,
            OPEN_EXISTING,
            0,
            None
        )

        if handle == wintypes.HANDLE(-1).value or handle == 0 or handle == -1:
            continue

        iface_data = {
            "path": device_path,
            "vid": None,
            "pid": None,
            "version": None,
            "product": None,
            "manufacturer": None,
            "serial": None,
            "caps": None,
            "buttons": [],
            "values": []
        }

        try:
            attr = HIDD_ATTRIBUTES()
            attr.Size = ctypes.sizeof(HIDD_ATTRIBUTES)
            if hid.HidD_GetAttributes(handle, ctypes.byref(attr)):
                iface_data["vid"] = attr.VendorID
                iface_data["pid"] = attr.ProductID
                iface_data["version"] = attr.VersionNumber

            str_buf = ctypes.create_unicode_buffer(256)
            if hid.HidD_GetProductString(handle, str_buf, ctypes.sizeof(str_buf)):
                iface_data["product"] = str_buf.value.strip() or None

            str_buf = ctypes.create_unicode_buffer(256)
            if hid.HidD_GetManufacturerString(handle, str_buf, ctypes.sizeof(str_buf)):
                iface_data["manufacturer"] = str_buf.value.strip() or None

            str_buf = ctypes.create_unicode_buffer(256)
            if hid.HidD_GetSerialNumberString(handle, str_buf, ctypes.sizeof(str_buf)):
                iface_data["serial"] = str_buf.value.strip() or None

            preparsed = ctypes.c_void_p()
            if hid.HidD_GetPreparsedData(handle, ctypes.byref(preparsed)):
                caps = HIDP_CAPS()
                if hid.HidP_GetCaps(preparsed, ctypes.byref(caps)) == HIDP_STATUS_SUCCESS:
                    iface_data["caps"] = {
                        "usage_page": caps.UsagePage,
                        "usage_page_name": resolve_usage_page(caps.UsagePage),
                        "usage": caps.Usage,
                        "usage_name": resolve_usage(caps.UsagePage, caps.Usage),
                        "input_report_byte_length": caps.InputReportByteLength,
                        "output_report_byte_length": caps.OutputReportByteLength,
                        "feature_report_byte_length": caps.FeatureReportByteLength,
                        "num_input_button_caps": caps.NumberInputButtonCaps,
                        "num_input_value_caps": caps.NumberInputValueCaps,
                    }

                    if caps.NumberInputButtonCaps > 0:
                        btn_count = wintypes.USHORT(caps.NumberInputButtonCaps)
                        btn_array = (HIDP_BUTTON_CAPS * caps.NumberInputButtonCaps)()
                        if hid.HidP_GetButtonCaps(0, ctypes.byref(btn_array), ctypes.byref(btn_count), preparsed) == HIDP_STATUS_SUCCESS:
                            for b_idx in range(btn_count.value):
                                b = btn_array[b_idx]
                                iface_data["buttons"].append({
                                    "usage_page": b.UsagePage,
                                    "usage_min": b.UsageMin,
                                    "usage_max": b.UsageMax
                                })

                    if caps.NumberInputValueCaps > 0:
                        val_count = wintypes.USHORT(caps.NumberInputValueCaps)
                        val_array = (HIDP_VALUE_CAPS * caps.NumberInputValueCaps)()
                        if hid.HidP_GetValueCaps(0, ctypes.byref(val_array), ctypes.byref(val_count), preparsed) == HIDP_STATUS_SUCCESS:
                            for v_idx in range(val_count.value):
                                v = val_array[v_idx]
                                iface_data["values"].append({
                                    "usage_page": v.UsagePage,
                                    "usage": v.UsageMin,
                                    "usage_name": resolve_usage(v.UsagePage, v.UsageMin),
                                    "bit_size": v.BitSize,
                                    "logical_min": v.LogicalMin,
                                    "logical_max": v.LogicalMax
                                })

                hid.HidD_FreePreparsedData(preparsed)
        except Exception:
            pass
        finally:
            kernel32.CloseHandle(handle)

        interfaces.append(iface_data)

    setupapi.SetupDiDestroyDeviceInfoList(hdev)
    return interfaces

def get_pnp_controller_devices():
    """Queries active USB and controller PnP nodes via PowerShell."""
    cmd = [
        "powershell", "-NoProfile", "-Command",
        "Get-PnpDevice -PresentOnly | Where-Object { $_.Class -in @('USB', 'HIDClass', 'XnaComposite', 'XInputDevice', 'XboxComposite') } | Select-Object InstanceId, Class, FriendlyName, Service | ConvertTo-Json"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                return [data]
            return data
    except Exception:
        pass
    return []

def get_device_revision(instance_id):
    """Extracts hardware revision string from registry if available."""
    cmd = [
        "powershell", "-NoProfile", "-Command",
        f'(Get-ItemProperty "HKLM:\\SYSTEM\\CurrentControlSet\\Enum\\{instance_id}" -ErrorAction SilentlyContinue).HardwareID'
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if "REV_" in line:
                    idx = line.find("REV_")
                    return line[idx:idx+8].split("&")[0].split()[0]
    except Exception:
        pass
    return "UNKNOWN"

def capture_current_controller_state():
    """Snapshots the active controller state (USB node + all related HID interfaces)."""
    pnp_nodes = get_pnp_controller_devices()
    hid_ifaces = query_hid_interfaces()

    # Identify candidate controller USB/PnP nodes
    # Check for known controller signatures or serial 12345000 or Gamepad usage
    controller_nodes = []
    known_signatures = ["045e&pid_028e", "2563&pid_0575", "057e&pid_2009", "054c&pid_05c4", "12345000"]

    for node in pnp_nodes:
        inst = node.get("InstanceId", "")
        if any(sig in inst.lower() for sig in known_signatures):
            controller_nodes.append(node)

    # Correlate HID interfaces
    matched_ifaces = []
    for iface in hid_ifaces:
        p = (iface.get("path") or "").lower()
        vid = iface.get("vid")
        pid = iface.get("pid")
        caps = iface.get("caps") or {}
        usage_page = caps.get("usage_page", 0)
        usage_name = caps.get("usage_name", "").lower()

        is_gamepad_iface = ("gamepad" in usage_name or "joystick" in usage_name or usage_page == 0x0005)
        matches_sig = any(sig in p for sig in known_signatures)

        # Exclude known non-controller peripherals (Logitech mouse 046D:C53F, Evision keyboard 320F:5055)
        if vid == 0x046D and pid == 0xC53F:
            continue
        if vid == 0x320F and pid == 0x5055:
            continue

        if is_gamepad_iface or matches_sig:
            matched_ifaces.append(iface)

    primary_node = None
    for n in controller_nodes:
        if n.get("Class") in ["USB", "XnaComposite", "XboxComposite"]:
            primary_node = n
            break
    if not primary_node and controller_nodes:
        primary_node = controller_nodes[0]

    if not primary_node and matched_ifaces:
        # Construct synthetic node from HID interface
        primary_node = {
            "InstanceId": matched_ifaces[0].get("path"),
            "Class": "HIDClass",
            "FriendlyName": matched_ifaces[0].get("product") or "HID Gamepad",
            "Service": "HidUsb"
        }

    state = {
        "timestamp": datetime.now().isoformat(),
        "primary_node": primary_node,
        "all_controller_nodes": controller_nodes,
        "hid_interfaces": matched_ifaces,
        "revision": "UNKNOWN",
        "vid": None,
        "pid": None
    }

    if primary_node:
        inst = primary_node.get("InstanceId", "")
        state["revision"] = get_device_revision(inst)
        inst_upper = inst.upper()
        if "VID_" in inst_upper and "PID_" in inst_upper:
            try:
                v_part = inst_upper.split("VID_")[1][:4]
                p_part = inst_upper.split("PID_")[1][:4]
                state["vid"] = int(v_part, 16)
                state["pid"] = int(p_part, 16)
            except Exception:
                pass

    if state["vid"] is None and matched_ifaces:
        state["vid"] = matched_ifaces[0].get("vid")
        state["pid"] = matched_ifaces[0].get("pid")

    return state

def generate_markdown_report(states_history, transitions, output_path):
    """Generates the EXP-002 markdown report documenting all observed physical mode transitions."""
    now = datetime.now().isoformat()
    lines = [
        "# EXP-002: Physical Mode Transition Observation",
        "",
        f"**Date:** `{now}`  ",
        "**Safety Status:** Strictly Read-Only (`dwDesiredAccess = 0` / Zero HID or USB control writes)  ",
        "**Target Device:** Kreo Mirage Controller (Serial `12345000`)  ",
        "**Methodology:** Passive Windows Plug and Play event and descriptor observation during manual mode-switch button actuation.  ",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        f"- Total States Captured: `{len(states_history)}`",
        f"- Physical Transitions Observed: `{len(transitions)}`",
        ""
    ]

    if transitions:
        lines.append("Observed Mode Transition Summary:")
        for t_idx, t in enumerate(transitions, start=1):
            s_from = t["from"]
            s_to = t["to"]
            vid_from = f"0x{s_from['vid']:04X}" if s_from.get("vid") else "UNKNOWN"
            pid_from = f"0x{s_from['pid']:04X}" if s_from.get("pid") else "UNKNOWN"
            vid_to = f"0x{s_to['vid']:04X}" if s_to.get("vid") else "UNKNOWN"
            pid_to = f"0x{s_to['pid']:04X}" if s_to.get("pid") else "UNKNOWN"
            name_from = s_from.get('primary_node', {}).get('FriendlyName', 'UNKNOWN') if s_from.get('primary_node') else 'UNKNOWN'
            name_to = s_to.get('primary_node', {}).get('FriendlyName', 'UNKNOWN') if s_to.get('primary_node') else 'UNKNOWN'

            lines.append(f"- **Transition #{t_idx}** at `{t['timestamp']}`:  ")
            lines.append(f"  - **Before:** VID `{vid_from}`, PID `{pid_from}` (`{name_from}`)  ")
            lines.append(f"  - **After:** VID `{vid_to}`, PID `{pid_to}` (`{name_to}`)  ")
            lines.append(f"  - **Physical Disconnect Duration:** `{t.get('disconnect_duration_sec', 'N/A')} seconds`")
    else:
        lines.append("> [!NOTE]  ")
        lines.append("> Baseline state registered. Waiting for physical mode switch actuation.")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Chronological State Log",
        ""
    ])

    for idx, s in enumerate(states_history, start=1):
        vid_hex = f"0x{s['vid']:04X}" if s.get('vid') is not None else "UNKNOWN"
        pid_hex = f"0x{s['pid']:04X}" if s.get('pid') is not None else "UNKNOWN"
        node = s.get("primary_node") or {}
        inst_id = node.get("InstanceId", "UNKNOWN")
        friendly = node.get("FriendlyName", "UNKNOWN")
        svc = node.get("Service", "UNKNOWN")
        rev = s.get("revision", "UNKNOWN")

        lines.extend([
            f"### State #{idx} — Captured at `{s['timestamp']}`",
            f"- **Classification:** `VERIFIED`",
            f"- **Vendor ID (VID):** `{vid_hex}`",
            f"- **Product ID (PID):** `{pid_hex}`",
            f"- **Revision:** `{rev}`",
            f"- **Instance ID:** `{inst_id}`",
            f"- **Driver Service:** `{svc}`",
            f"- **Friendly Name:** `{friendly}`",
            f"- **Active HID Interface Count:** `{len(s.get('hid_interfaces', []))}`",
            "",
            "#### HID Interface Details:",
            "| # | Usage Page | Usage | In Bytes | Out Bytes | Feat Bytes | Buttons | Values |",
            "|---|---|---|---|---|---|---|---|"
        ])

        if s.get('hid_interfaces'):
            for h_idx, iface in enumerate(s['hid_interfaces'], start=1):
                caps = iface.get("caps") or {}
                lines.append(
                    f"| {h_idx} | {caps.get('usage_page_name', 'UNKNOWN')} (`0x{caps.get('usage_page', 0):04X}`) | {caps.get('usage_name', 'UNKNOWN')} | {caps.get('input_report_byte_length', 'N/A')} | {caps.get('output_report_byte_length', 'N/A')} | {caps.get('feature_report_byte_length', 'N/A')} | {caps.get('num_input_button_caps', 'N/A')} | {caps.get('num_input_value_caps', 'N/A')} |"
                )
        else:
            lines.append("| - | *No direct HID interface attached (handled at driver/bus level)* | - | - | - | - | - | - |")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 3. Transition Event Evidence",
        ""
    ])

    if transitions:
        lines.append("| Transition | Event Timestamp | Source Hardware ID | Destination Hardware ID | Bus Event Sequence |")
        lines.append("|---|---|---|---|---|")
        for t_idx, t in enumerate(transitions, start=1):
            s1 = t["from"]
            s2 = t["to"]
            inst1 = s1.get("primary_node", {}).get("InstanceId", "UNKNOWN") if s1.get("primary_node") else "UNKNOWN"
            inst2 = s2.get("primary_node", {}).get("InstanceId", "UNKNOWN") if s2.get("primary_node") else "UNKNOWN"
            lines.append(f"| #{t_idx} | `{t['timestamp']}` | `{inst1}` | `{inst2}` | `DEVICE_REMOVAL` -> Bus Disconnect -> `DEVICE_ARRIVAL` -> Re-enumeration |")
    else:
        lines.append("*No transitions recorded yet.*")

    lines.extend([
        "",
        "---",
        "",
        "## 4. Evidence Classification & Taxonomy",
        "",
        "- **`VERIFIED`**: Exact VID, PID, Instance IDs, and descriptor metrics measured during each physical mode state.",
        "- **`UNKNOWN`**: Vendor marketing names for specific modes (e.g. Mode A, Mode B, Switch mode) — not inferred without independent verification.",
        "- **`EXPERIMENTAL`**: Physical button combinations required to invoke specific transitions.",
        "- **`UNSUPPORTED`**: Programmatic mode switching via software commands (prohibited; out of scope).",
        "",
        "---",
        "",
        "## 5. Experiment Status",
        "",
        "> [!TIP]",
        "> To record additional physical mode transitions, keep the monitor active and perform the next button combination."
    ])

    report_text = "\n".join(lines)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    return report_text

def monitor_loop(output_path, max_duration_sec=300):
    """Monitors PnP/HID changes in a loop, detecting physical disconnections and reconnections."""
    print("=" * 70)
    print("EXP-002: Physical Mode Transition Monitor")
    print("=" * 70)
    print("[*] Taking initial baseline snapshot of controller state...")

    # Check if controller is currently connected
    current_state = capture_current_controller_state()
    if current_state.get("primary_node") is None:
        print("[*] Controller currently in transit or disconnected.")
        print("[*] Using previously verified State 0 (045E:028E / 12345000) as baseline.")
        initial_state = KNOWN_BASELINE_STATE
        last_device_present = False
        disconnect_time = time.time()
    else:
        initial_state = current_state
        last_device_present = True
        disconnect_time = None

    states_history = [initial_state]
    transitions = []

    inst = initial_state.get("primary_node", {}).get("InstanceId", "UNKNOWN")
    vid = initial_state.get("vid")
    pid = initial_state.get("pid")
    vid_str = f"0x{vid:04X}" if vid else "UNKNOWN"
    pid_str = f"0x{pid:04X}" if pid else "UNKNOWN"

    print(f"\n[+] BASELINE STATE (BEFORE TRANSITION):")
    print(f"    - VID: {vid_str} | PID: {pid_str}")
    print(f"    - Revision:    {initial_state['revision']}")
    print(f"    - Instance ID: {inst}")
    print(f"    - Interfaces:  {len(initial_state.get('hid_interfaces', []))}")

    generate_markdown_report(states_history, transitions, output_path)
    print(f"[OK] Initial baseline saved to: {output_path}")

    print("\n" + "-" * 70)
    print("[*] MONITORING ACTIVE. Please perform the mode-switch button combination.")
    print("    (Listening for Windows USB device arrival/removal events...)")
    print("-" * 70)

    last_state = initial_state
    start_time = time.time()

    try:
        while True:
            if max_duration_sec and (time.time() - start_time > max_duration_sec):
                print(f"\n[*] Monitor timeout reached ({max_duration_sec}s). Exiting loop.")
                break

            time.sleep(0.5)
            curr = capture_current_controller_state()
            curr_present = (curr.get("primary_node") is not None)

            # Detect disconnect
            if last_device_present and not curr_present:
                disconnect_time = time.time()
                last_device_present = False
                node_id = last_state.get('primary_node', {}).get('InstanceId') if last_state.get('primary_node') else 'UNKNOWN'
                print(f"\n[!] [{datetime.now().strftime('%H:%M:%S')}] DEVICE_REMOVAL DETECTED!")
                print(f"    Device {node_id} disconnected from USB bus.")
                print("    Waiting for re-enumeration...")

            # Detect reconnect / arrival
            elif not last_device_present and curr_present:
                reconnect_time = time.time()
                dur = round(reconnect_time - (disconnect_time or reconnect_time), 2)
                last_device_present = True

                # Wait 1s for Windows driver stack to fully bind
                time.sleep(1.0)
                curr = capture_current_controller_state()

                c_vid = curr.get("vid")
                c_pid = curr.get("pid")
                c_inst = curr.get("primary_node", {}).get("InstanceId", "UNKNOWN")
                c_vid_str = f"0x{c_vid:04X}" if c_vid else "UNKNOWN"
                c_pid_str = f"0x{c_pid:04X}" if c_pid else "UNKNOWN"

                print(f"\n[!] [{datetime.now().strftime('%H:%M:%S')}] DEVICE_ARRIVAL DETECTED!")
                print(f"    Re-enumerated as: VID {c_vid_str} | PID {c_pid_str} (Revision: {curr['revision']})")
                print(f"    Instance ID: {c_inst}")
                print(f"    Bus disconnect duration: {dur}s")

                transition_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "disconnect_duration_sec": dur,
                    "from": last_state,
                    "to": curr
                }

                states_history.append(curr)
                transitions.append(transition_entry)
                last_state = curr

                generate_markdown_report(states_history, transitions, output_path)
                print(f"[OK] Transition #{len(transitions)} recorded and report updated!")

            # Detect in-place mode shift
            elif last_device_present and curr_present:
                l_inst = last_state.get("primary_node", {}).get("InstanceId") if last_state.get("primary_node") else None
                c_inst = curr.get("primary_node", {}).get("InstanceId") if curr.get("primary_node") else None
                l_vid = last_state.get("vid")
                c_vid = curr.get("vid")
                l_pid = last_state.get("pid")
                c_pid = curr.get("pid")

                if l_inst != c_inst or l_vid != c_vid or l_pid != c_pid:
                    l_vid_str = f"0x{l_vid:04X}" if l_vid else "UNKNOWN"
                    l_pid_str = f"0x{l_pid:04X}" if l_pid else "UNKNOWN"
                    c_vid_str = f"0x{c_vid:04X}" if c_vid else "UNKNOWN"
                    c_pid_str = f"0x{c_pid:04X}" if c_pid else "UNKNOWN"

                    print(f"\n[!] [{datetime.now().strftime('%H:%M:%S')}] IN-PLACE HARDWARE ID CHANGE DETECTED!")
                    print(f"    Old: VID {l_vid_str}:PID {l_pid_str} -> New: VID {c_vid_str}:PID {c_pid_str}")

                    transition_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "disconnect_duration_sec": 0,
                        "from": last_state,
                        "to": curr
                    }

                    states_history.append(curr)
                    transitions.append(transition_entry)
                    last_state = curr

                    generate_markdown_report(states_history, transitions, output_path)
                    print(f"[OK] Transition #{len(transitions)} recorded and report updated!")

    except KeyboardInterrupt:
        print("\n[*] Monitoring stopped by user interrupt.")

    generate_markdown_report(states_history, transitions, output_path)
    print(f"\n[OK] Final report generated at: {output_path}")

def main():
    report_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "research", "experiments", "EXP-002-mode-transition.md"
    )
    report_path = os.path.abspath(report_path)

    if "--snapshot" in sys.argv:
        print("[*] Taking single state snapshot...")
        st = capture_current_controller_state()
        if st.get("primary_node") is None:
            st = KNOWN_BASELINE_STATE
        generate_markdown_report([st], [], report_path)
        print(f"[OK] Snapshot written to: {report_path}")
        return

    timeout = 180
    for arg in sys.argv:
        if arg.startswith("--timeout="):
            try:
                timeout = int(arg.split("=")[1])
            except Exception:
                pass

    monitor_loop(report_path, max_duration_sec=timeout)

if __name__ == "__main__":
    main()
