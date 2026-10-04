"""
COWL Core Protocol Engine
Handles parsing and normalization of DualShock 4 (State 2: 054C:05C4) HID reports.
"""

# DPAD HAT switch lookup table: 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW, 8=Released
DPAD_MAP = {
    0: (True, False, False, False),   # Up, Down, Left, Right
    1: (True, False, False, True),
    2: (False, False, False, True),
    3: (False, True, False, True),
    4: (False, True, False, False),
    5: (False, True, True, False),
    6: (False, False, True, False),
    7: (True, False, True, False),
    8: (False, False, False, False),
}

def parse_ds4_input_report(data: bytes) -> dict | None:
    """
    Parses a 64-byte DualShock 4 USB input report.
    Accepts packets with or without 0x01 Report ID header.
    Returns normalized dictionary of controller inputs.
    """
    if not data or len(data) < 10:
        return None

    # Handle optional leading report ID byte (0x01)
    offset = 1 if data[0] == 0x01 else 0
    if len(data) < offset + 9:
        return None

    # Analog sticks (0..255, center 128) -> normalized (-1.0 .. +1.0)
    lx = (data[offset] - 128) / 128.0
    ly = -(data[offset + 1] - 128) / 128.0  # Invert Y so up is positive
    rx = (data[offset + 2] - 128) / 128.0
    ry = -(data[offset + 3] - 128) / 128.0

    # Byte 5: D-pad (bits 0-3) and face buttons (bits 4-7)
    b5 = data[offset + 4]
    dpad_up, dpad_down, dpad_left, dpad_right = DPAD_MAP.get(b5 & 0x0F, (False, False, False, False))
    btn_x = bool(b5 & 0x10)  # Square (X on Xbox)
    btn_a = bool(b5 & 0x20)  # Cross (A on Xbox)
    btn_b = bool(b5 & 0x40)  # Circle (B on Xbox)
    btn_y = bool(b5 & 0x80)  # Triangle (Y on Xbox)

    # Byte 6: Shoulders, triggers (digital), menu buttons, thumb clicks
    b6 = data[offset + 5]
    lb = bool(b6 & 0x01)     # L1
    rb = bool(b6 & 0x02)     # R1
    back = bool(b6 & 0x10)   # Share / View
    start = bool(b6 & 0x20)  # Options / Menu
    l3 = bool(b6 & 0x40)     # LThumb click
    r3 = bool(b6 & 0x80)     # RThumb click

    # Byte 7: Guide / PS button
    b7 = data[offset + 6]
    guide = bool(b7 & 0x01)  # Home / Guide

    # Bytes 8 & 9: Analog triggers (0..255) -> (0.0 .. 1.0)
    lt = data[offset + 7] / 255.0
    rt = data[offset + 8] / 255.0

    return {
        'lx': max(-1.0, min(1.0, lx)),
        'ly': max(-1.0, min(1.0, ly)),
        'rx': max(-1.0, min(1.0, rx)),
        'ry': max(-1.0, min(1.0, ry)),
        'dpad_up': dpad_up,
        'dpad_down': dpad_down,
        'dpad_left': dpad_left,
        'dpad_right': dpad_right,
        'btn_a': btn_a,
        'btn_b': btn_b,
        'btn_x': btn_x,
        'btn_y': btn_y,
        'lb': lb,
        'rb': rb,
        'back': back,
        'start': start,
        'l3': l3,
        'r3': r3,
        'guide': guide,
        'lt': max(0.0, min(1.0, lt)),
        'rt': max(0.0, min(1.0, rt)),
    }
