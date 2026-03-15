# DevStat — Device Stats

A lightweight Python tool for Linux that detects connected devices and displays
key information: USB, Bluetooth, Android phones (via ADB), and system battery.

---

## Features

| Category   | Info Displayed                                              |
|------------|-------------------------------------------------------------|
| All devices| Name, Manufacturer, Connection type                         |
| Battery    | Percentage, Charging state                                  |
| Android    | Battery %, Charging, SIM present/absent, Carrier, Bluetooth |
| Bluetooth  | Paired/connected devices, MAC address, adapter state        |
| USB        | Enumerated USB devices via `lsusb`                          |

---

## Installation

### From RPM (Fedora / RHEL / openSUSE)

```bash
sudo dnf install python3-tkinter python3-psutil
sudo rpm -ivh devstat-1.0-1.noarch.rpm
```

### From Source

```bash
git clone https://github.com/example/devstat.git
cd devstat
pip install -e .
```

### Optional Dependencies

| Feature          | Dependency                     |
|------------------|-------------------------------|
| Android via ADB  | `android-tools` (system pkg)   |
| Bluetooth        | `bluez` / `bluetoothctl`       |
| BLE scanning     | `pip install bleak`            |

---

## Usage

### GUI

```bash
devstat gui
# or just:
devstat
```

### CLI

```bash
devstat scan              # Scan all devices
devstat usb               # USB devices only
devstat bluetooth         # Bluetooth devices
devstat android           # Android phones via ADB
devstat battery           # System battery
devstat export report.json       # Export JSON report
devstat export report.txt --txt  # Export plain-text report
```

### Example Output

```
────────────────────────────────────────────
[1] Pixel 6
Manufacturer:  Google
Connection:    USB

Battery:       82%
Charging:      Yes ⚡

SIM:           Present
Carrier:       T-Mobile

Bluetooth:     Enabled
────────────────────────────────────────────
```

---

## Building the RPM

```bash
# Install build tools
sudo dnf install rpm-build python3-setuptools

# Create tarball
cd /path/to/devstat
tar czf ~/rpmbuild/SOURCES/devstat-1.0.tar.gz \
    --transform 's,^,devstat-1.0/,' \
    devstat/ setup.py README.md LICENSE

# Build RPM
rpmbuild -ba rpm/SPECS/devstat.spec

# Install
sudo rpm -ivh ~/rpmbuild/RPMS/noarch/devstat-1.0-1.noarch.rpm
```

---

## Project Structure

```
devstat/
├── devstat/
│   ├── __init__.py      # Package info
│   ├── detector.py      # Device detection logic
│   ├── gui.py           # Tkinter GUI
│   ├── cli.py           # CLI interface
│   └── exporter.py      # JSON / TXT export
├── devstat.py           # Entry point
├── setup.py             # setuptools config
├── rpm/
│   └── SPECS/
│       └── devstat.spec # RPM spec
└── README.md
```

---

## Requirements

- Python 3.8+
- Linux (tested on Fedora, Ubuntu, Arch)
- `python3-tkinter` for GUI
- `psutil` for system battery
- `pyusb` for USB (supplement to `lsusb`)
- `lsusb` system command (usually pre-installed)
- `bluetoothctl` for Bluetooth (part of `bluez`)
- `adb` for Android detection (`android-tools`)

---

## Ubuntu Install ( UnTested )

```
# Add the repo
echo "deb [trusted=yes] https://hatd3v.github.io/devstat/repo/apt ./" | sudo tee /etc/apt/sources.list.d/devstat.list

# Update package list
sudo apt update

# Install
sudo apt install devstat
```

## License

MIT
