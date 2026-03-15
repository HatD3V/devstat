"""
devstat/cli.py
Command-line interface for DevStat.

Usage:
    devstat scan                        # Scan all devices
    devstat usb                         # USB devices only
    devstat bluetooth                   # Bluetooth devices only
    devstat android                     # Android devices via ADB
    devstat battery                     # System battery
    devstat export report.json          # Scan all and export JSON
    devstat export report.txt --txt     # Scan all and export plain text
    devstat gui                         # Launch Tkinter GUI
"""

import argparse
import sys

from .detector import (
    scan_all, detect_usb_devices, detect_bluetooth_devices,
    detect_android_devices, detect_system_battery, DeviceInfo,
)
from .exporter import export_json, export_text

# ── ANSI colours ─────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
GRAY   = "\033[90m"


def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if _supports_color():
        return f"{code}{text}{RESET}"
    return text


def _print_device(dev: DeviceInfo, index: int):
    sep = _c(GRAY, "─" * 44)
    print(sep)
    print(_c(BOLD + CYAN, f"[{index}] {dev.name}"))
    print(f"{_c(GRAY, 'Manufacturer:')}  {dev.manufacturer}")
    print(f"{_c(GRAY, 'Connection:')}    {_c(BLUE, dev.connection)}")

    if dev.battery is not None or dev.charging is not None:
        print()
        if dev.battery is not None:
            pct = dev.battery
            col = GREEN if pct >= 60 else YELLOW if pct >= 20 else RED
            print(f"{_c(GRAY, 'Battery:')}       {_c(col, str(pct) + '%')}")
        if dev.charging is not None:
            val = _c(GREEN, "Yes ⚡") if dev.charging else _c(GRAY, "No")
            print(f"{_c(GRAY, 'Charging:')}      {val}")

    if dev.sim_present is not None or dev.carrier:
        print()
        if dev.sim_present is not None:
            val = _c(GREEN, "Present") if dev.sim_present else _c(RED, "Absent")
            print(f"{_c(GRAY, 'SIM:')}           {val}")
        if dev.carrier:
            print(f"{_c(GRAY, 'Carrier:')}       {dev.carrier}")

    if dev.bluetooth_enabled is not None:
        print()
        val = _c(GREEN, "Enabled") if dev.bluetooth_enabled else _c(GRAY, "Disabled")
        print(f"{_c(GRAY, 'Bluetooth:')}     {val}")

    if dev.extra:
        print()
        for k, v in dev.extra.items():
            print(f"{_c(GRAY, k + ':')}{'':>4} {v}")


def _print_devices(devices):
    if not devices:
        print(_c(YELLOW, "No devices found."))
        return
    print(_c(BOLD, f"\nDevStat — {len(devices)} device(s) found\n"))
    for i, dev in enumerate(devices, 1):
        _print_device(dev, i)
    print(_c(GRAY, "─" * 44))


def main():
    parser = argparse.ArgumentParser(
        prog="devstat",
        description="DevStat — Linux Device Stats Inspector",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("scan",      help="Scan all connected devices")
    sub.add_parser("usb",       help="List USB devices")
    sub.add_parser("bluetooth", help="List Bluetooth devices")
    sub.add_parser("android",   help="List Android devices via ADB")
    sub.add_parser("battery",   help="Show system battery status")
    sub.add_parser("gui",       help="Launch the Tkinter GUI")

    exp_p = sub.add_parser("export", help="Scan all and export a report")
    exp_p.add_argument("output", help="Output file path (e.g. report.json)")
    exp_p.add_argument("--txt", action="store_true", help="Export as plain text instead of JSON")

    args = parser.parse_args()

    if args.command == "gui":
        from .gui import launch
        launch()
        return

    commands = {
        "scan":      scan_all,
        "usb":       detect_usb_devices,
        "bluetooth": detect_bluetooth_devices,
        "android":   detect_android_devices,
        "battery":   detect_system_battery,
    }

    if args.command in commands:
        devices = commands[args.command]()
        _print_devices(devices)

    elif args.command == "export":
        print("Scanning all devices…")
        devices = scan_all()
        _print_devices(devices)
        if args.txt:
            path = export_text(devices, args.output)
            print(_c(GREEN, f"\n✓ Text report saved to: {path}"))
        else:
            path = export_json(devices, args.output)
            print(_c(GREEN, f"\n✓ JSON report saved to: {path}"))

    else:
        # No subcommand — default to scan
        devices = scan_all()
        _print_devices(devices)


if __name__ == "__main__":
    main()
