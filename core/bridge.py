"""
COWL Controller Bridge (Ultra-Low Latency Engine)
Manages connection to the physical Kreo Mirage controller and drives the
virtual Xbox 360 gamepad via ViGEmBus with zero queue lag (<1ms latency).
"""
import time
import threading
import hid
import vgamepad as vg
from core.protocol import parse_ds4_input_report

VID_SONY_DS4 = 0x054C
PID_SONY_DS4 = 0x05C4

VID_MS_X360 = 0x045E
PID_MS_X360 = 0x028E

# Pre-allocated tuple to eliminate allocation overhead in the fast path
BTN_BINDINGS = (
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
)

class ControllerBridge:
    def __init__(self):
        self.running = False
        self.virtual_enabled = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        
        self.device_state = "DISCONNECTED" # DISCONNECTED | PS4_MODE | XINPUT_MODE
        self.device_info = {}
        self._hid_device = None
        self._vgamepad: vg.VX360Gamepad | None = None

        self.last_parsed_input = None
        self.status_callback = None

    def set_virtual_xinput(self, enabled: bool):
        """Toggle the virtual Xbox 360 controller."""
        with self._lock:
            self.virtual_enabled = enabled
            if enabled:
                if self._vgamepad is None:
                    try:
                        self._vgamepad = vg.VX360Gamepad()
                    except Exception as e:
                        print(f"[COWL Bridge] Error spawning VX360Gamepad: {e}")
            else:
                if self._vgamepad is not None:
                    try:
                        del self._vgamepad
                    except Exception:
                        pass
                    self._vgamepad = None

        self._notify_status()

    def start(self):
        """Start the background poll and bridge thread."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the bridge and release virtual controllers."""
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._close_device()
        with self._lock:
            if self._vgamepad is not None:
                del self._vgamepad
                self._vgamepad = None

    def _notify_status(self):
        if self.status_callback:
            try:
                self.status_callback(self.device_state, self.virtual_enabled, self.device_info)
            except Exception:
                pass

    def _close_device(self):
        if self._hid_device is not None:
            try:
                self._hid_device.close()
            except Exception:
                pass
            self._hid_device = None

    def _find_mirage(self):
        """Enumerate devices to find Kreo Mirage in either state."""
        try:
            devs = hid.enumerate()
        except Exception:
            return None, None

        # Check for State 2 (PS4 mode)
        for d in devs:
            if d['vendor_id'] == VID_SONY_DS4 and d['product_id'] == PID_SONY_DS4:
                if d.get('interface_number', -1) == 3 or d.get('usage', 0) == 5 or d.get('usage_page', 0) == 1:
                    return "PS4_MODE", d

        # Check for State 1 (Native XInput mode)
        for d in devs:
            if d['vendor_id'] == VID_MS_X360 and d['product_id'] == PID_MS_X360:
                return "XINPUT_MODE", d

        return "DISCONNECTED", None

    def _run_loop(self):
        while self.running:
            # 1. Connection check (only executed when NOT in active PS4 streaming loop)
            mode, dev_info = self._find_mirage()
            if mode != self.device_state:
                self.device_state = mode
                self.device_info = dev_info or {}
                if mode != "PS4_MODE":
                    self._close_device()
                self._notify_status()

            if mode == "DISCONNECTED":
                time.sleep(0.5)
                continue

            if mode == "XINPUT_MODE":
                time.sleep(0.5)
                continue

            # mode == "PS4_MODE" -> Open device once
            if self._hid_device is None and dev_info:
                try:
                    self._hid_device = hid.device()
                    self._hid_device.open_path(dev_info['path'])
                    self._hid_device.set_nonblocking(False)
                except Exception as e:
                    self._hid_device = None
                    time.sleep(0.5)
                    continue

            # FAST ULTRA-LOW LATENCY STREAMING LOOP
            # Never call hid.enumerate() while connected!
            while self.running and self._hid_device is not None:
                try:
                    # Read with short 2ms timeout
                    raw = self._hid_device.read(64, 2)
                    if not raw:
                        time.sleep(0.001)
                        continue

                    # Drain queue: keep only the latest report to eliminate any buffered lag
                    latest_raw = raw
                    while True:
                        queued = self._hid_device.read(64, 0) # non-blocking
                        if queued:
                            latest_raw = queued
                        else:
                            break

                    parsed = parse_ds4_input_report(bytes(latest_raw))
                    if parsed:
                        self.last_parsed_input = parsed
                        with self._lock:
                            if self.virtual_enabled and self._vgamepad is not None:
                                self._apply_inputs_to_vgamepad(parsed)

                except Exception as e:
                    # Device unplugged or reset
                    self._close_device()
                    self.device_state = "DISCONNECTED"
                    self._notify_status()
                    break

    def _apply_inputs_to_vgamepad(self, parsed: dict):
        gp = self._vgamepad
        gp.reset()
        gp.left_joystick_float(parsed['lx'], parsed['ly'])
        gp.right_joystick_float(parsed['rx'], parsed['ry'])
        gp.left_trigger_float(parsed['lt'])
        gp.right_trigger_float(parsed['rt'])

        for key, xusb_btn in BTN_BINDINGS:
            if parsed.get(key, False):
                gp.press_button(xusb_btn)

        gp.update()
