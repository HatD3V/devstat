Name:           devstat
Version:        1.0
Release:        1%{?dist}
Summary:        Linux device stats inspector — USB, Bluetooth, Android, Battery

License:        MIT
URL:            https://github.com/example/devstat
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

Requires:       python3 >= 3.8
Requires:       python3-tkinter
Requires:       python3-psutil
Requires:       python3-pyusb
# Optional runtime deps (best-effort; won't fail install if absent):
# android-tools (adb), bluez (bluetoothctl)

%description
DevStat is a Python tool for Linux that detects connected devices and displays
key information including device name, manufacturer, battery level, charging
state, SIM status, carrier, and Bluetooth status.

Supports:
  - USB devices (via lsusb)
  - Bluetooth paired/connected devices (via bluetoothctl)
  - Android phones (via adb)
  - System battery (via psutil)

Includes both a Tkinter GUI and a full CLI interface.

%prep
%autosetup

%build
%py3_build

%install
%py3_install

# Install the CLI wrapper to /usr/bin/devstat
install -d %{buildroot}/usr/bin
cat > %{buildroot}/usr/bin/devstat << 'EOF'
#!/usr/bin/env python3
from devstat.cli import main
main()
EOF
chmod 0755 %{buildroot}/usr/bin/devstat

# Desktop entry for GUI launch
install -d %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/devstat.desktop << 'EOF'
[Desktop Entry]
Name=DevStat
Comment=Device Stats Inspector
Exec=/usr/bin/devstat gui
Icon=system-devices
Terminal=false
Type=Application
Categories=System;HardwareSettings;
EOF

%files
%license LICENSE
%doc README.md
/usr/bin/devstat
%{python3_sitelib}/devstat/
%{python3_sitelib}/devstat-*.egg-info/
%{_datadir}/applications/devstat.desktop

%changelog
* Sat Mar 14 2026 DevStat Maintainer <maintainer@example.com> - 1.0-1
- Initial release
- USB device detection via lsusb
- Bluetooth detection via bluetoothctl
- Android detection via adb
- System battery via psutil
- Tkinter GUI with scan, detail view, and JSON/TXT export
- CLI: scan, usb, bluetooth, android, battery, export, gui
