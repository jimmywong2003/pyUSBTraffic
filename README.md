# USB Traffic Generator
A Python script to generate heavy USB traffic on a specific port for stress testing, particularly targeting the Lumidigm fingerprint reader.

## Overview
This script uses the PyUSB library to generate heavy USB traffic on a specific port connected to a Lumidigm fingerprint reader. It provides a simple GUI to control the traffic generation process.

## Features
- Find and configure the Lumidigm fingerprint reader
- Generate heavy USB traffic to stress test the USB bus
- Simple GUI to start and stop traffic generation
- Detailed logging for debugging and monitoring

## Requirements
- Python 3.6 or higher
- PyUSB library
- libusb backend (libusb-1.0.dll for Windows)
- Lumidigm fingerprint reader (VID: 0x1FAE, PID: 0x0013)

## Installation
1. Install Python:
   - Download and install Python from python.org.
   - Ensure Python is added to your system PATH during installation.

2. Install PyUSB:
   ```bash
   pip install pyusb
   ```

3. Install libusb:
   - Download the latest libusb Windows installer from the libusb GitHub releases page.
   - Extract the downloaded file and copy the libusb-1.0.dll file to C:\Windows\System32.

## Usage
1. Run the Script:
   - Open Command Prompt as Administrator.
   - Navigate to the directory containing the script and run:
   ```bash
   python pyUSBTraffic.py
   ```

2. Using the GUI:
   - Click Start Traffic to begin generating USB traffic.
   - Click Stop Traffic to halt the traffic generation.

## Troubleshooting
- **Error: No backend available**:
  - Ensure libusb is installed and the libusb-1.0.dll file is in C:\Windows\System32.
  - Run the script as Administrator.

- **Error: Lumidigm device not found**:
  - Ensure the Lumidigm fingerprint reader is properly connected.
  - Check the device VID and PID in the script.

- **Error: Operation not supported or unimplemented on this platform**:
  - Check if the device driver is up-to-date.
  - Ensure the device is compatible with Windows 11.
  - Try connecting the device to a different USB port.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
