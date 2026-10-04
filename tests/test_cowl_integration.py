"""
COWL Integration and Self-Check Suite
Validates protocol engine, bridge lifecycle, and virtual gamepad creation.
"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.protocol import parse_ds4_input_report
from core.bridge import ControllerBridge

def test_protocol_bounds():
    # Test empty or malformed inputs
    assert parse_ds4_input_report(b"") is None
    assert parse_ds4_input_report(b"\x00" * 5) is None
    
    # Test valid neutral packet
    neutral = bytearray(64)
    neutral[0] = 0x01
    neutral[1] = 128
    neutral[2] = 128
    neutral[3] = 128
    neutral[4] = 128
    neutral[5] = 0x08 # Dpad released
    p = parse_ds4_input_report(bytes(neutral))
    assert p is not None
    assert p['btn_a'] is False
    assert p['dpad_up'] is False
    print("[PASS] Protocol boundary assertions verified.")

def test_bridge_lifecycle():
    bridge = ControllerBridge()
    # Test starting and stopping without hardware
    bridge.start()
    assert bridge.running is True
    time.sleep(0.1)

    # Test toggling virtual XInput
    bridge.set_virtual_xinput(True)
    assert bridge.virtual_enabled is True
    assert bridge._vgamepad is not None
    print("[PASS] Virtual Xbox 360 gamepad successfully spawned on ViGEmBus.")

    # Test toggling OFF
    bridge.set_virtual_xinput(False)
    assert bridge.virtual_enabled is False
    assert bridge._vgamepad is None
    print("[PASS] Virtual Xbox 360 gamepad successfully released.")

    bridge.stop()
    assert bridge.running is False
    print("[PASS] Bridge lifecycle cleanly terminated.")

if __name__ == '__main__':
    test_protocol_bounds()
    test_bridge_lifecycle()
    print("\nALL COWL INTEGRATION TESTS PASSED!")
