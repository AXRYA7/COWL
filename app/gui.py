"""
COWL — Desktop GUI Application (Decoupled, Zero-Lag)
Lightweight, zero-bloat controller mode switcher interface.
"""
import tkinter as tk
from tkinter import ttk
import sys
import os

# Ensure repo root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.bridge import ControllerBridge

class CowlApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("COWL — Controller Mode Switcher")
        self.root.geometry("460x520")
        self.root.resizable(False, False)
        self.root.configure(bg="#14171A")

        self.bridge = ControllerBridge()
        self.bridge.status_callback = self._on_bridge_status

        self._build_ui()
        self.bridge.start()
        
        # Start decoupled 30 FPS diagnostic polling
        self._poll_diagnostics()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Header banner
        header_frame = tk.Frame(self.root, bg="#1E2328", padx=20, pady=16)
        header_frame.pack(fill="x")

        title_lbl = tk.Label(
            header_frame,
            text="COWL",
            font=("Segoe UI", 18, "bold"),
            fg="#00E5FF",
            bg="#1E2328"
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(
            header_frame,
            text="Hardware Bridge & Mode Switcher for Kreo Mirage",
            font=("Segoe UI", 9),
            fg="#8A939E",
            bg="#1E2328"
        )
        subtitle_lbl.pack(anchor="w")

        # Main content
        content_frame = tk.Frame(self.root, bg="#14171A", padx=20, pady=16)
        content_frame.pack(fill="both", expand=True)

        # Connection Status Card
        status_card = tk.LabelFrame(
            content_frame,
            text=" Controller Status ",
            font=("Segoe UI", 9, "bold"),
            fg="#A0AAB5",
            bg="#1E2328",
            padx=16,
            pady=12,
            relief="solid",
            bd=1
        )
        status_card.pack(fill="x", pady=(0, 16))

        self.status_dot = tk.Label(status_card, text="●", font=("Segoe UI", 16), fg="#FF5252", bg="#1E2328")
        self.status_dot.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.status_title = tk.Label(
            status_card,
            text="Waiting for Controller...",
            font=("Segoe UI", 11, "bold"),
            fg="#FFFFFF",
            bg="#1E2328"
        )
        self.status_title.grid(row=0, column=1, sticky="w")

        self.status_desc = tk.Label(
            status_card,
            text="Plug in your Kreo Mirage controller via USB.",
            font=("Segoe UI", 9),
            fg="#8A939E",
            bg="#1E2328",
            wraplength=360,
            justify="left"
        )
        self.status_desc.grid(row=1, column=1, sticky="w", pady=(2, 0))

        # Mode Switch / Toggle Card
        toggle_card = tk.LabelFrame(
            content_frame,
            text=" Mode Configuration ",
            font=("Segoe UI", 9, "bold"),
            fg="#A0AAB5",
            bg="#1E2328",
            padx=16,
            pady=16,
            relief="solid",
            bd=1
        )
        toggle_card.pack(fill="x", pady=(0, 16))

        self.mode_desc_lbl = tk.Label(
            toggle_card,
            text="Toggle between native PlayStation mode and virtual Xbox 360 mode:",
            font=("Segoe UI", 9),
            fg="#CFD8DC",
            bg="#1E2328",
            wraplength=380,
            justify="left"
        )
        self.mode_desc_lbl.pack(anchor="w", pady=(0, 12))

        # Toggle Button
        self.toggle_btn = tk.Button(
            toggle_card,
            text="Virtual Xbox 360 (XInput): OFF",
            font=("Segoe UI", 11, "bold"),
            bg="#374151",
            fg="#9CA3AF",
            activebackground="#4B5563",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            command=self._on_toggle_click
        )
        self.toggle_btn.pack(fill="x")

        self.output_status_lbl = tk.Label(
            toggle_card,
            text="Output: Native DualShock 4 (DirectInput)",
            font=("Segoe UI", 8),
            fg="#8A939E",
            bg="#1E2328"
        )
        self.output_status_lbl.pack(pady=(8, 0))

        # Live Input Diagnostics Card
        diag_card = tk.LabelFrame(
            content_frame,
            text=" Live Hardware Diagnostics ",
            font=("Segoe UI", 9, "bold"),
            fg="#A0AAB5",
            bg="#1E2328",
            padx=16,
            pady=10,
            relief="solid",
            bd=1
        )
        diag_card.pack(fill="x")

        self.sticks_lbl = tk.Label(
            diag_card,
            text="Left Stick: (0.00, 0.00) | Right Stick: (0.00, 0.00)",
            font=("Consolas", 8),
            fg="#00E5FF",
            bg="#1E2328"
        )
        self.sticks_lbl.pack(anchor="w")

        self.triggers_lbl = tk.Label(
            diag_card,
            text="LT: 0.00 | RT: 0.00",
            font=("Consolas", 8),
            fg="#00E5FF",
            bg="#1E2328"
        )
        self.triggers_lbl.pack(anchor="w")

        self.buttons_lbl = tk.Label(
            diag_card,
            text="Buttons: None",
            font=("Consolas", 8),
            fg="#8A939E",
            bg="#1E2328"
        )
        self.buttons_lbl.pack(anchor="w")

    def _on_toggle_click(self):
        new_state = not self.bridge.virtual_enabled
        self.bridge.set_virtual_xinput(new_state)

    def _on_bridge_status(self, device_state: str, virtual_enabled: bool, dev_info: dict):
        self.root.after(0, self._apply_status_ui, device_state, virtual_enabled, dev_info)

    def _apply_status_ui(self, device_state: str, virtual_enabled: bool, dev_info: dict):
        if device_state == "PS4_MODE":
            self.status_dot.config(text="●", fg="#00E5FF")
            self.status_title.config(text="Kreo Mirage Connected (PS4 Mode)")
            self.status_desc.config(
                text="Hardware VID: 0x054C | PID: 0x05C4. Low-latency bridge active."
            )
            self.toggle_btn.config(state="normal")
        elif device_state == "XINPUT_MODE":
            self.status_dot.config(text="●", fg="#00E676")
            self.status_title.config(text="Kreo Mirage Connected (Native XInput)")
            self.status_desc.config(
                text="Hardware VID: 0x045E | PID: 0x028E. Operating natively in Windows."
            )
            self.toggle_btn.config(state="disabled")
        else: # DISCONNECTED
            self.status_dot.config(text="●", fg="#FF5252")
            self.status_title.config(text="No Controller Detected")
            self.status_desc.config(
                text="Plug in your Kreo Mirage controller via USB."
            )
            self.toggle_btn.config(state="normal")

        if virtual_enabled:
            self.toggle_btn.config(
                text="Virtual Xbox 360 (XInput): ACTIVE",
                bg="#00C853",
                fg="#FFFFFF",
                activebackground="#00B248"
            )
            self.output_status_lbl.config(
                text="Output: Virtual Xbox 360 via ViGEmBus (<1ms latency)",
                fg="#00E676"
            )
        else:
            self.toggle_btn.config(
                text="Virtual Xbox 360 (XInput): OFF",
                bg="#374151",
                fg="#9CA3AF",
                activebackground="#4B5563"
            )
            self.output_status_lbl.config(
                text="Output: Native DualShock 4 (DirectInput)",
                fg="#8A939E"
            )

    def _poll_diagnostics(self):
        """Steady 30 FPS GUI refresh without touching fast input loop."""
        p = self.bridge.last_parsed_input
        if p:
            self.sticks_lbl.config(
                text=f"Left Stick: ({p['lx']:+.2f}, {p['ly']:+.2f}) | Right Stick: ({p['rx']:+.2f}, {p['ry']:+.2f})"
            )
            self.triggers_lbl.config(
                text=f"LT: {p['lt']:.2f} | RT: {p['rt']:.2f}"
            )
            active_btns = []
            for b in ['btn_a', 'btn_b', 'btn_x', 'btn_y', 'lb', 'rb', 'back', 'start', 'guide']:
                if p.get(b):
                    active_btns.append(b.upper().replace('BTN_', ''))
            self.buttons_lbl.config(
                text=f"Buttons: {', '.join(active_btns) if active_btns else 'None'}",
                fg="#00E676" if active_btns else "#8A939E"
            )

        # Schedule next update in 33ms (~30 FPS)
        self.root.after(33, self._poll_diagnostics)

    def _on_close(self):
        self.bridge.stop()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = CowlApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
