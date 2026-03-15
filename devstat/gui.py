"""
devstat/gui.py
Tkinter GUI for DevStat.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from typing import List, Optional

from .detector import DeviceInfo, scan_all, detect_usb_devices, detect_bluetooth_devices, detect_android_devices, detect_system_battery
from .exporter import export_json, export_text


# ── Palette ───────────────────────────────────────────────────────────────────
BG         = "#0f1117"
BG2        = "#1a1d27"
BG3        = "#252836"
ACCENT     = "#4f8ef7"
ACCENT2    = "#6ee7b7"
TEXT       = "#e2e8f0"
TEXT_DIM   = "#64748b"
BORDER     = "#2d3144"
SUCCESS    = "#22c55e"
WARNING    = "#f59e0b"
DANGER     = "#ef4444"

FONT_TITLE  = ("SF Pro Display", 20, "bold")
FONT_HEADER = ("SF Pro Display", 12, "bold")
FONT_BODY   = ("SF Pro Text",   10)
FONT_MONO   = ("JetBrains Mono", 9)
FONT_SMALL  = ("SF Pro Text",   9)

# Fallback font stack
def _font(preferred, size, weight="normal"):
    return (preferred, size, weight)


class DevStatApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DevStat — Device Stats")
        self.geometry("960x620")
        self.minsize(780, 480)
        self.configure(bg=BG)
        self._devices: List[DeviceInfo] = []
        self._selected: Optional[DeviceInfo] = None
        self._build_ui()
        self._apply_styles()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Title bar ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG, pady=0)
        header.pack(fill=tk.X, padx=0, pady=0)

        title_row = tk.Frame(header, bg=BG)
        title_row.pack(fill=tk.X, padx=24, pady=(18, 4))

        tk.Label(
            title_row, text="DevStat", bg=BG, fg=ACCENT,
            font=("Courier New", 22, "bold")
        ).pack(side=tk.LEFT)
        tk.Label(
            title_row, text=" — Device Stats", bg=BG, fg=TEXT_DIM,
            font=("Courier New", 14)
        ).pack(side=tk.LEFT, pady=(6, 0))

        # Divider
        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X)

        # ── Toolbar ────────────────────────────────────────────────────────────
        toolbar = tk.Frame(self, bg=BG2, pady=8)
        toolbar.pack(fill=tk.X)

        btn_frame = tk.Frame(toolbar, bg=BG2)
        btn_frame.pack(side=tk.LEFT, padx=16)

        self._btn_scan = self._make_button(btn_frame, "⟳  Scan All", self._scan_all, primary=True)
        self._btn_scan.pack(side=tk.LEFT, padx=(0, 8))

        self._make_button(btn_frame, "USB",       lambda: self._scan(detect_usb_devices)).pack(side=tk.LEFT, padx=4)
        self._make_button(btn_frame, "Bluetooth", lambda: self._scan(detect_bluetooth_devices)).pack(side=tk.LEFT, padx=4)
        self._make_button(btn_frame, "Android",   lambda: self._scan(detect_android_devices)).pack(side=tk.LEFT, padx=4)
        self._make_button(btn_frame, "Battery",   lambda: self._scan(detect_system_battery)).pack(side=tk.LEFT, padx=4)

        right_frame = tk.Frame(toolbar, bg=BG2)
        right_frame.pack(side=tk.RIGHT, padx=16)
        self._make_button(right_frame, "⤓  Export JSON", self._export_json).pack(side=tk.RIGHT, padx=(4, 0))
        self._make_button(right_frame, "⤓  Export TXT",  self._export_txt).pack(side=tk.RIGHT, padx=4)

        # Status
        self._status_var = tk.StringVar(value="Ready — press Scan All to begin.")
        tk.Label(
            toolbar, textvariable=self._status_var, bg=BG2,
            fg=TEXT_DIM, font=("Courier New", 9), anchor="w"
        ).pack(side=tk.LEFT, padx=16)

        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X)

        # ── Main pane ──────────────────────────────────────────────────────────
        pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=BG, sashwidth=4,
                              sashrelief=tk.FLAT, bd=0)
        pane.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Left: device list
        left = tk.Frame(pane, bg=BG2, width=260)
        left.pack_propagate(False)
        pane.add(left, minsize=200)

        tk.Label(
            left, text="CONNECTED DEVICES", bg=BG2, fg=TEXT_DIM,
            font=("Courier New", 8, "bold"), anchor="w", padx=16, pady=8
        ).pack(fill=tk.X)
        tk.Frame(left, bg=BORDER, height=1).pack(fill=tk.X)

        list_frame = tk.Frame(left, bg=BG2)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=4)

        scrollbar = tk.Scrollbar(list_frame, bg=BG3, troughcolor=BG2, relief=tk.FLAT, bd=0)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._listbox = tk.Listbox(
            list_frame,
            bg=BG2, fg=TEXT,
            font=("Courier New", 10),
            selectbackground=BG3,
            selectforeground=ACCENT,
            activestyle="none",
            relief=tk.FLAT, bd=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
            cursor="hand2",
        )
        self._listbox.pack(fill=tk.BOTH, expand=True, padx=0)
        scrollbar.config(command=self._listbox.yview)
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

        # Count badge
        self._count_var = tk.StringVar(value="0 devices")
        tk.Label(
            left, textvariable=self._count_var, bg=BG2, fg=TEXT_DIM,
            font=("Courier New", 8), anchor="w", padx=16, pady=6
        ).pack(fill=tk.X)

        # Right: detail panel
        right = tk.Frame(pane, bg=BG)
        pane.add(right, minsize=300)

        tk.Label(
            right, text="DEVICE DETAILS", bg=BG, fg=TEXT_DIM,
            font=("Courier New", 8, "bold"), anchor="w", padx=24, pady=8
        ).pack(fill=tk.X)
        tk.Frame(right, bg=BORDER, height=1).pack(fill=tk.X)

        detail_scroll_frame = tk.Frame(right, bg=BG)
        detail_scroll_frame.pack(fill=tk.BOTH, expand=True)

        detail_sb = tk.Scrollbar(detail_scroll_frame, bg=BG3, troughcolor=BG, relief=tk.FLAT, bd=0)
        detail_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._detail_text = tk.Text(
            detail_scroll_frame,
            bg=BG, fg=TEXT,
            font=("Courier New", 11),
            relief=tk.FLAT, bd=0,
            highlightthickness=0,
            wrap=tk.WORD,
            state=tk.DISABLED,
            padx=24, pady=16,
            yscrollcommand=detail_sb.set,
            cursor="arrow",
            spacing1=4, spacing3=4,
        )
        self._detail_text.pack(fill=tk.BOTH, expand=True)
        detail_sb.config(command=self._detail_text.yview)

        # Configure text tags for coloring
        self._detail_text.tag_configure("heading",  foreground=ACCENT,  font=("Courier New", 13, "bold"))
        self._detail_text.tag_configure("label",    foreground=TEXT_DIM, font=("Courier New", 10))
        self._detail_text.tag_configure("value",    foreground=TEXT,     font=("Courier New", 11, "bold"))
        self._detail_text.tag_configure("ok",       foreground=SUCCESS)
        self._detail_text.tag_configure("warn",     foreground=WARNING)
        self._detail_text.tag_configure("err",      foreground=DANGER)
        self._detail_text.tag_configure("dim",      foreground=TEXT_DIM)
        self._detail_text.tag_configure("section",  foreground=ACCENT2,  font=("Courier New", 9, "bold"))
        self._detail_text.tag_configure("divider",  foreground=BORDER)

        self._show_placeholder()

        # ── Footer ─────────────────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X)
        footer = tk.Frame(self, bg=BG, pady=5)
        footer.pack(fill=tk.X)
        tk.Label(
            footer, text="DevStat v1.0  ·  Linux Device Inspector",
            bg=BG, fg=TEXT_DIM, font=("Courier New", 8)
        ).pack(side=tk.LEFT, padx=16)

    # ── Styling ───────────────────────────────────────────────────────────────

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

    def _make_button(self, parent, text, command, primary=False):
        bg_col  = ACCENT  if primary else BG3
        fg_col  = "#fff"  if primary else TEXT
        act_bg  = "#3b74e0" if primary else BORDER

        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg_col, fg=fg_col, activebackground=act_bg, activeforeground=fg_col,
            font=("Courier New", 9, "bold"),
            relief=tk.FLAT, bd=0, padx=12, pady=6,
            cursor="hand2",
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=act_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg_col))
        return btn

    # ── Scanning ──────────────────────────────────────────────────────────────

    def _scan_all(self):
        self._scan(scan_all)

    def _scan(self, fn):
        self._set_status("Scanning…")
        self._btn_scan.config(state=tk.DISABLED, text="Scanning…")
        self._listbox.delete(0, tk.END)
        self._show_placeholder()

        def worker():
            try:
                devices = fn()
            except Exception as exc:
                devices = []
                self.after(0, lambda: messagebox.showerror("Scan Error", str(exc)))
            self.after(0, lambda: self._populate(devices))

        threading.Thread(target=worker, daemon=True).start()

    def _populate(self, devices: List[DeviceInfo]):
        self._devices = devices
        self._listbox.delete(0, tk.END)

        icons = {"USB": "⬛", "Bluetooth": "◈", "System": "⚡"}
        for dev in devices:
            icon = icons.get(dev.connection, "•")
            self._listbox.insert(tk.END, f"  {icon}  {dev.name}")

        count = len(devices)
        self._count_var.set(f"{count} device{'s' if count != 1 else ''} found")
        self._set_status(f"Scan complete — {count} device{'s' if count != 1 else ''} found.")
        self._btn_scan.config(state=tk.NORMAL, text="⟳  Scan All")

        if devices:
            self._listbox.selection_set(0)
            self._show_device(devices[0])
        else:
            self._show_placeholder("No devices found.")

    def _on_select(self, event):
        sel = self._listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if 0 <= idx < len(self._devices):
            self._show_device(self._devices[idx])

    # ── Detail Panel ──────────────────────────────────────────────────────────

    def _tw(self, text, tag=None):
        """Write to detail text widget."""
        self._detail_text.config(state=tk.NORMAL)
        if tag:
            self._detail_text.insert(tk.END, text, tag)
        else:
            self._detail_text.insert(tk.END, text)
        self._detail_text.config(state=tk.DISABLED)

    def _tc(self):
        self._detail_text.config(state=tk.NORMAL)
        self._detail_text.delete("1.0", tk.END)
        self._detail_text.config(state=tk.DISABLED)

    def _show_placeholder(self, msg="Select a device from the list."):
        self._tc()
        self._tw("\n\n  " + msg, "dim")

    def _row(self, label: str, value: str, value_tag="value"):
        self._tw(f"  {label:<16}", "label")
        self._tw(value + "\n", value_tag)

    def _show_device(self, dev: DeviceInfo):
        self._tc()
        self._tw(f"\n  {dev.name}\n", "heading")
        self._tw("  " + "─" * 36 + "\n", "divider")
        self._tw("\n")

        self._tw("  IDENTIFICATION\n", "section")
        self._row("Device", dev.name)
        self._row("Manufacturer", dev.manufacturer)
        conn_tag = "ok" if dev.connection == "USB" else "warn" if dev.connection == "Bluetooth" else "value"
        self._row("Connection", dev.connection, conn_tag)

        if dev.battery is not None or dev.charging is not None:
            self._tw("\n  POWER\n", "section")
            if dev.battery is not None:
                pct = dev.battery
                tag = "ok" if pct >= 60 else "warn" if pct >= 20 else "err"
                bar = self._battery_bar(pct)
                self._row("Battery", f"{pct}%  {bar}", tag)
            if dev.charging is not None:
                self._row("Charging", "Yes ⚡" if dev.charging else "No", "ok" if dev.charging else "dim")

        if dev.sim_present is not None or dev.carrier:
            self._tw("\n  CELLULAR\n", "section")
            if dev.sim_present is not None:
                self._row("SIM", "Present ✓" if dev.sim_present else "Absent", "ok" if dev.sim_present else "err")
            if dev.carrier:
                self._row("Carrier", dev.carrier)

        if dev.bluetooth_enabled is not None:
            self._tw("\n  WIRELESS\n", "section")
            self._row("Bluetooth", "Enabled ◈" if dev.bluetooth_enabled else "Disabled", "ok" if dev.bluetooth_enabled else "dim")

        if dev.extra:
            self._tw("\n  EXTRAS\n", "section")
            for k, v in dev.extra.items():
                self._row(k, str(v))

        self._tw("\n  " + "─" * 36 + "\n", "divider")

    @staticmethod
    def _battery_bar(pct: int) -> str:
        filled = round(pct / 10)
        return "[" + "█" * filled + "░" * (10 - filled) + "]"

    # ── Export ────────────────────────────────────────────────────────────────

    def _export_json(self):
        if not self._devices:
            messagebox.showwarning("No Data", "Run a scan first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="devstat_report.json",
        )
        if path:
            out = export_json(self._devices, path)
            messagebox.showinfo("Exported", f"Report saved to:\n{out}")

    def _export_txt(self):
        if not self._devices:
            messagebox.showwarning("No Data", "Run a scan first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="devstat_report.txt",
        )
        if path:
            out = export_text(self._devices, path)
            messagebox.showinfo("Exported", f"Report saved to:\n{out}")

    # ── Status ────────────────────────────────────────────────────────────────

    def _set_status(self, msg: str):
        self._status_var.set(msg)


def launch():
    app = DevStatApp()
    app.mainloop()
