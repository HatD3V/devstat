from setuptools import setup, find_packages

setup(
    name="devstat",
    version="1.0.1",
    description="Linux device stats inspector — USB, Bluetooth, Android, Battery",
    author="DevStat",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9",
        "pyusb>=1.2",
        # bleak is optional (BT LE scanning); bluetoothctl covers paired devices
        # adb-shell is optional; system adb binary used by default
    ],
    entry_points={
        "console_scripts": [
            "devstat=devstat.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications",
        "Topic :: System :: Hardware",
    ],
)
