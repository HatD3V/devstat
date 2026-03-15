"""
devstat/exporter.py
Exports device scan results to JSON (and optionally plain text).
"""

import json
import os
from datetime import datetime
from typing import List
from .detector import DeviceInfo


def export_json(devices: List[DeviceInfo], path: str) -> str:
    """Export device list to a JSON file. Returns the absolute path written."""
    path = os.path.abspath(path)
    payload = {
        "generated": datetime.now().isoformat(),
        "device_count": len(devices),
        "devices": [d.to_dict() for d in devices],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return path


def export_text(devices: List[DeviceInfo], path: str) -> str:
    """Export device list to a plain-text file. Returns absolute path."""
    path = os.path.abspath(path)
    lines = [
        "DevStat Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 40,
        "",
    ]
    for dev in devices:
        lines.extend(dev.display_lines())
        lines.append("-" * 40)
        lines.append("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path
