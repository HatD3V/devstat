"""
devstat/detector.py
Handles detection of USB, Bluetooth, Android (ADB), and system battery devices.
"""

import subprocess
import json
import re
import os
from dataclasses import dataclass, field, asdict
from typing import Optional, List


@dataclass
class DeviceInfo:
    name: str
    manufacturer: str
    connection: str                   # USB | Bluetooth | System
    battery: Optional[int] = None     # percentage
    charging: Optional[bool] = None
    sim_present: Optional[bool] = None
    carrier: Optional[str] = None
    bluetooth_enabled: Optional[bool] = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def display_lines(self) -> List[str]:
        lines = []
        lines.append(f"Device:       {self.name}")
        lines.append(f"Manufacturer: {self.manufacturer}")
        lines.append(f"Connection:   {self.connection}")
        lines.append("")
        if self.battery is not None:
            lines.append(f"Battery:      {self.battery}%")
        if self.charging is not None:
            lines.append(f"Charging:     {'Yes' if self.charging else 'No'}")
        if self.sim_present is not None:
            lines.append("")
            lines.append(f"SIM:          {'Present' if self.sim_present else 'Absent'}")
        if self.carrier:
            lines.append(f"Carrier:      {self.carrier}")
        if self.bluetooth_enabled is not None:
            lines.append("")
            lines.append(f"Bluetooth:    {'Enabled' if self.bluetooth_enabled else 'Disabled'}")
        for k, v in self.extra.items():
            lines.append(f"{k+':':<14}{v}")
        return lines


# ── Helpers ──────────────────────────────────────────────────────────────────

def _run(cmd: List[str], timeout: int = 6) -> Optional[str]:
    """Run a subprocess and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
        return None


# ── USB Detection ─────────────────────────────────────────────────────────────

def detect_usb_devices() -> List[DeviceInfo]:
    """Use lsusb to enumerate USB devices."""
    devices = []
    output = _run(["lsusb"])
    if not output:
        return devices

    for line in output.splitlines():
        # Bus 001 Device 002: ID 18d1:4ee7 Google LLC Nexus/Pixel Device
        m = re.match(
            r"Bus\s+\d+\s+Device\s+\d+:\s+ID\s+[\da-f:]+\s+(.*)", line, re.I
        )
        if not m:
            continue
        full_name = m.group(1).strip()
        if not full_name or full_name.lower() in ("linux foundation root hub", ""):
            continue

        # Split "Manufacturer Model..."  heuristically at first space
        parts = full_name.split(None, 1)
        manufacturer = parts[0] if parts else "Unknown"
        name = parts[1] if len(parts) > 1 else full_name

        dev = DeviceInfo(
            name=name or full_name,
            manufacturer=manufacturer,
            connection="USB",
        )
        devices.append(dev)

    return devices


# ── Bluetooth Detection ───────────────────────────────────────────────────────

def detect_bluetooth_devices() -> List[DeviceInfo]:
    """Use bluetoothctl to list paired/connected BT devices."""
    devices = []

    # Check if bluetooth service is running
    bt_status = _run(["systemctl", "is-active", "bluetooth"])
    bt_enabled = bt_status == "active"

    output = _run(["bluetoothctl", "devices"])
    if not output:
        # Return a placeholder showing BT status
        devices.append(DeviceInfo(
            name="Bluetooth Adapter",
            manufacturer="System",
            connection="Bluetooth",
            bluetooth_enabled=bt_enabled,
        ))
        return devices

    for line in output.splitlines():
        # Device AA:BB:CC:DD:EE:FF DeviceName
        m = re.match(r"Device\s+([\dA-Fa-f:]{17})\s+(.*)", line)
        if not m:
            continue
        mac, name = m.group(1), m.group(2).strip()

        # Try to get more info
        info_out = _run(["bluetoothctl", "info", mac])
        connected = False
        manufacturer = "Unknown"
        if info_out:
            for info_line in info_out.splitlines():
                if "Connected: yes" in info_line:
                    connected = True
                if "Alias:" in info_line:
                    name = info_line.split("Alias:")[1].strip() or name

        dev = DeviceInfo(
            name=name,
            manufacturer=manufacturer,
            connection="Bluetooth",
            bluetooth_enabled=bt_enabled,
            extra={"MAC": mac, "Connected": "Yes" if connected else "No"},
        )
        devices.append(dev)

    if not devices:
        devices.append(DeviceInfo(
            name="No paired devices",
            manufacturer="—",
            connection="Bluetooth",
            bluetooth_enabled=bt_enabled,
        ))
    return devices


# ── ADB / Android Detection ───────────────────────────────────────────────────

def detect_android_devices() -> List[DeviceInfo]:
    """Use adb to detect connected Android phones."""
    devices = []

    adb_out = _run(["adb", "devices", "-l"])
    if not adb_out:
        return devices

    lines = adb_out.splitlines()
    for line in lines[1:]:  # skip header
        if not line.strip() or "offline" in line:
            continue
        parts = line.split()
        if len(parts) < 2 or parts[1] not in ("device", "recovery"):
            continue

        serial = parts[0]

        # Gather device properties
        def adb_prop(prop: str) -> Optional[str]:
            return _run(["adb", "-s", serial, "shell", "getprop", prop])

        model = adb_prop("ro.product.model") or "Android Device"
        manufacturer = adb_prop("ro.product.manufacturer") or "Unknown"

        # Battery
        battery_out = _run(["adb", "-s", serial, "shell", "dumpsys", "battery"])
        battery_pct: Optional[int] = None
        charging: Optional[bool] = None
        if battery_out:
            for bline in battery_out.splitlines():
                if "level:" in bline:
                    try:
                        battery_pct = int(bline.split(":")[1].strip())
                    except ValueError:
                        pass
                if "status:" in bline:
                    try:
                        status_code = int(bline.split(":")[1].strip())
                        charging = status_code == 2  # 2 = CHARGING
                    except ValueError:
                        pass

        # SIM / carrier
        sim_out = _run(
            ["adb", "-s", serial, "shell", "dumpsys", "telephony.registry"]
        )
        sim_present = False
        carrier: Optional[str] = None
        if sim_out:
            sim_present = "mSimState=5" in sim_out or "READY" in sim_out
            m_carrier = re.search(r"mNetworkOperatorName=([^\n\r]+)", sim_out)
            if m_carrier:
                carrier = m_carrier.group(1).strip() or None

        # Bluetooth state on phone
        bt_out = _run(
            ["adb", "-s", serial, "shell", "settings", "get", "global", "bluetooth_on"]
        )
        bt_enabled = bt_out == "1" if bt_out else None

        dev = DeviceInfo(
            name=model,
            manufacturer=manufacturer.capitalize(),
            connection="USB",
            battery=battery_pct,
            charging=charging,
            sim_present=sim_present,
            carrier=carrier,
            bluetooth_enabled=bt_enabled,
            extra={"Serial": serial},
        )
        devices.append(dev)

    return devices


# ── System Battery ────────────────────────────────────────────────────────────

def detect_system_battery() -> List[DeviceInfo]:
    """Detect laptop/system battery using psutil."""
    devices = []
    try:
        import psutil
        batt = psutil.sensors_battery()
        if batt is None:
            return devices
        dev = DeviceInfo(
            name="System Battery",
            manufacturer="System",
            connection="System",
            battery=int(batt.percent),
            charging=batt.power_plugged,
        )
        devices.append(dev)
    except ImportError:
        pass
    except Exception:
        pass
    return devices


# ── Master Scan ───────────────────────────────────────────────────────────────

def scan_all() -> List[DeviceInfo]:
    """Run all detectors and return a combined list."""
    results: List[DeviceInfo] = []
    results.extend(detect_system_battery())
    results.extend(detect_android_devices())
    results.extend(detect_usb_devices())
    results.extend(detect_bluetooth_devices())
    return results
