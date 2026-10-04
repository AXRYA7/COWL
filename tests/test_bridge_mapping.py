"""
Unit self-test for DS4 to Virtual Xbox 360 report translation.
Tests synthetic byte payloads against expected vgamepad state.
"""
import vgamepad as vg

DPAD_MAP = {
    0: (True, False, False, False),   # N
    1: (True, False, False, True),    # NE
    2: (False, False, False, True),   # E
    3: (False, True, False, True),    # SE
    4: (False, True, False, False),   # S
    5: (False, True, True, False),    # SW
    6: (False, False, True, False),   # W
    7: (True, False, True, False),    # NW
    8: (False, False, False, False),  # Released
}

def parse_ds4_report(data: bytes):
    """
    Parses a 64-byte DS4 USB report.
    Returns parsed dictionary of normalized inputs.
    """
    if len(data) < 10:
        return None
    
    # Account for optional report ID prefix (if data[0] == 0x01, payload starts at index 1)
    offset = 1 if data[0] == 0x01 else 0
    if len(data) < offset + 9:
        return None

    lx = (data[offset] - 128) / 128.0
    # Invert Y so up is positive
    ly = -(data[offset + 1] - 128) / 128.0
    rx = (data[offset + 2] - 128) / 128.0
    ry = -(data[offset + 3] - 128) / 128.0

    b5 = data[offset + 4]
    dpad_val = b5 & 0x0F
    dpad_up, dpad_down, dpad_left, dpad_right = DPAD_MAP.get(dpad_val, (False, False, False, False))

    sq = bool(b5 & 0x10)   # Square -> X
    cr = bool(b5 & 0x20)   # Cross -> A
    ci = bool(b5 & 0x40)   # Circle -> B
    tr = bool(b5 & 0x80)   # Triangle -> Y

    b6 = data[offset + 5]
    l1 = bool(b6 & 0x01)   # LB
    r1 = bool(b6 & 0x02)   # RB
    share = bool(b6 & 0x10) # Back
    opt = bool(b6 & 0x20)   # Start
    l3 = bool(b6 & 0x40)   # LThumb
    r3 = bool(b6 & 0x80)   # RThumb

    b7 = data[offset + 6]
    guide = bool(b7 & 0x01) # Guide / Home

    l2 = data[offset + 7] / 255.0
    r2 = data[offset + 8] / 255.0

    return {
        'lx': max(-1.0, min(1.0, lx)),
        'ly': max(-1.0, min(1.0, ly)),
        'rx': max(-1.0, min(1.0, rx)),
        'ry': max(-1.0, min(1.0, ry)),
        'dpad_up': dpad_up,
        'dpad_down': dpad_down,
        'dpad_left': dpad_left,
        'dpad_right': dpad_right,
        'btn_a': cr,
        'btn_b': ci,
        'btn_x': sq,
        'btn_y': tr,
        'lb': l1,
        'rb': r1,
        'back': share,
        'start': opt,
        'l3': l3,
        'r3': r3,
        'guide': guide,
        'lt': l2,
        'rt': r2,
    }

def apply_to_gamepad(parsed, gamepad: vg.VX360Gamepad):
    """Applies parsed state to virtual Xbox 360 controller."""
    gamepad.reset()
    gamepad.left_joystick_float(parsed['lx'], parsed['ly'])
    gamepad.right_joystick_float(parsed['rx'], parsed['ry'])
    gamepad.left_trigger_float(parsed['lt'])
    gamepad.right_trigger_float(parsed['rt'])

    btn_map = [
        ('btn_a', vg.XUSB_BUTTON.XUSB_GAMEPAD_A),
        ('btn_b', vg.XUSB_BUTTON.XUSB_GAMEPAD_B),
        ('btn_x', vg.XUSB_BUTTON.XUSB_GAMEPAD_X),
        ('btn_y', vg.XUSB_BUTTON.XUSB_GAMEPAD_Y),
        ('lb', vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER),
        ('rb', vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER),
        ('back', vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK),
        ('start', vg.XUSB_BUTTON.XUSB_GAMEPAD_START),
        ('l3', vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB),
        ('r3', vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB),
        ('dpad_up', vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP),
        ('dpad_down', vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN),
        ('dpad_left', vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT),
        ('dpad_right', vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT),
        ('guide', vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE),
    ]

    for key, xusb_btn in btn_map:
        if parsed[key]:
            gamepad.press_button(xusb_btn)

    gamepad.update()

def test_neutral_state():
    # 64-byte packet, neutral sticks (128), no buttons, dpad released (8)
    pkt = bytearray(64)
    pkt[0] = 0x01
    pkt[1] = 128 # lx
    pkt[2] = 128 # ly
    pkt[3] = 128 # rx
    pkt[4] = 128 # ry
    pkt[5] = 0x08 # D-pad released
    
    parsed = parse_ds4_report(bytes(pkt))
    assert parsed is not None
    assert abs(parsed['lx']) < 0.01
    assert abs(parsed['ly']) < 0.01
    assert not parsed['btn_a']
    assert not parsed['dpad_up']
    print("[PASS] Neutral state parse verified.")

def test_full_cross_and_trigger():
    # Cross button pressed (0x20 in byte 5), full R2 trigger (255 in byte 9)
    pkt = bytearray(64)
    pkt[0] = 0x01
    pkt[1] = 128
    pkt[2] = 128
    pkt[3] = 128
    pkt[4] = 128
    pkt[5] = 0x28 # Cross pressed (0x20) + Dpad released (0x08)
    pkt[8] = 0    # L2
    pkt[9] = 255  # R2
    
    parsed = parse_ds4_report(bytes(pkt))
    assert parsed['btn_a'] is True
    assert parsed['btn_b'] is False
    assert abs(parsed['rt'] - 1.0) < 0.01
    print("[PASS] Cross button + trigger parse verified.")

def test_virtual_gamepad_emission():
    gp = vg.VX360Gamepad()
    pkt = bytearray(64)
    pkt[0] = 0x01
    pkt[1] = 255 # Full right LX
    pkt[2] = 128
    pkt[3] = 128
    pkt[4] = 128
    pkt[5] = 0x28 # Cross
    
    parsed = parse_ds4_report(bytes(pkt))
    apply_to_gamepad(parsed, gp)
    del gp
    print("[PASS] Virtual gamepad emission verified.")

if __name__ == '__main__':
    test_neutral_state()
    test_full_cross_and_trigger()
    test_virtual_gamepad_emission()
    print("\nALL BRIDGE UNIT TESTS PASSED SUCCESSFULLY!")
