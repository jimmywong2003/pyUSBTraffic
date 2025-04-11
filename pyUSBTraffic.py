import usb.core
import usb.util
import usb.backend.libusb1
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import random
import time
import os
import platform
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('usb_traffic.log'),
        logging.StreamHandler()
    ]
)

# Lumidigm device identifiers
LUMIDIGM_VID = 0x1FAE
LUMIDIGM_PID = 0x0013

class USBTrafficGenerator:
    def __init__(self):
        """Initialize the USB traffic generator"""
        self.running = False
        self.device = None
        self.packet_count = 0
        self.byte_count = 0
        self.backend = None
        self._setup_complete = False
        self.traffic_thread = None
        logging.info("USBTrafficGenerator initialized")

    def setup_backend(self):
        """Configure the libusb backend"""
        logging.info("Setting up libusb backend")
        try:
            if platform.system() == 'Windows':
                libusb_paths = [
                    "C:\\Windows\\System32\\libusb-1.0.dll",
                    os.path.expandvars("%ProgramFiles%\\LibUSB-Win32\\bin\\libusb-1.0.dll"),
                    os.path.expandvars("%ProgramFiles(x86)%\\LibUSB-Win32\\bin\\libusb-1.0.dll")
                ]
                
                for path in libusb_paths:
                    if os.path.exists(path):
                        self.backend = usb.backend.libusb1.get_backend(find_library=lambda x: path)
                        logging.info(f"Found libusb-1.0.dll at {path}")
                        break
                if self.backend is None:
                    logging.error("libusb-1.0.dll not found")
                    messagebox.showerror("Error", "libusb-1.0.dll not found. Please install libusb.")
                    return False
            else:
                self.backend = usb.backend.libusb1.get_backend()
                logging.info("Using default libusb backend")
            
            self._setup_complete = True
            logging.info("Backend setup complete")
            return True
        except Exception as e:
            logging.error(f"Backend setup failed: {str(e)}")
            messagebox.showerror("Error", f"Backend setup failed:\n{str(e)}")
            return False

    def find_device(self):
        """Find and configure the Lumidigm device"""
        logging.info("Searching for Lumidigm device")
        try:
            if not self._setup_complete and not self.setup_backend():
                return False
            
            # Find all devices first for debugging
            all_devices = list(usb.core.find(find_all=True, backend=self.backend))
            logging.info("Connected USB devices:")
            for dev in all_devices:
                logging.info(f"  VID={hex(dev.idVendor)}, PID={hex(dev.idProduct)}")
            
            # Find our specific device
            self.device = usb.core.find(
                idVendor=LUMIDIGM_VID,
                idProduct=LUMIDIGM_PID,
                backend=self.backend
            )
            
            if self.device is None:
                logging.error("Lumidigm device not found")
                messagebox.showerror("Error", "Lumidigm device not found")
                return False
                
            logging.info("Lumidigm device found, attempting to configure...")
            
            # Windows-specific configuration
            if platform.system() == 'Windows':
                # Reset the device first
                try:
                    self.device.reset()
                    logging.info("Device reset")
                except:
                    logging.warning("Device reset failed")
                    pass
                
                # Set configuration (Windows often needs this)
                try:
                    self.device.set_configuration()
                    logging.info("Device configuration set")
                except usb.core.USBError as e:
                    logging.warning(f"Configuration warning: {e}")
            
            # For Linux/Mac
            else:
                if self.device.is_kernel_driver_active(0):
                    self.device.detach_kernel_driver(0)
                    logging.info("Kernel driver detached")
                self.device.set_configuration()
                logging.info("Device configuration set")
            
            logging.info("Device configured successfully")
            return True
            
        except Exception as e:
            logging.error(f"Device configuration failed: {str(e)}")
            messagebox.showerror("Error", f"Device configuration failed:\n{str(e)}")
            return False

    def generate_traffic(self):
        """Generate USB traffic to the device"""
        if self.device is None:
            logging.error("No device found")
            return
            
        try:
            cfg = self.device.get_active_configuration()
            intf = cfg[(0, 0)]
            
            # Find endpoints
            ep_out = None
            ep_in = None
            
            for ep in intf:
                if usb.util.endpoint_type(ep.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK:
                    if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                        ep_out = ep
                    else:
                        ep_in = ep
            
            if not ep_out:
                logging.error("No output endpoint found")
                messagebox.showerror("Error", "No output endpoint found")
                return
                logging.info(f"Using endpoints - OUT: 0x{ep_out.bEndpointAddress:02x}, IN: 0x{ep_in.bEndpointAddress:02x if ep_in else 'None'}")
            
            logging.info("Starting traffic generation")
            while self.running:
                try:
                    # Generate and send data
                    data = bytes([random.getrandbits(8) for _ in range(64)])  # Fixed 64-byte packets
                    written = self.device.write(ep_out.bEndpointAddress, data, timeout=1000)
                    self.packet_count += 1
                    self.byte_count += written
                    logging.debug(f"Sent packet: {self.packet_count}, bytes: {written}")
                    
                    # Try to read if input endpoint exists
                    if ep_in:
                        try:
                            data_in = self.device.read(ep_in.bEndpointAddress, 64, timeout=1000)
                            self.byte_count += len(data_in)
                            logging.debug(f"Received data: {len(data_in)} bytes")
                        except usb.core.USBError as e:
                            if e.errno != -7:  # Ignore timeout errors
                                raise
                                logging.error(f"Read error: {e}")
                    
                    time.sleep(0.05)  # Small delay to prevent overwhelming
                    
                except usb.core.USBError as e:
                    logging.error(f"USB Error: {e}")
                    break
                except Exception as e:
                    logging.error(f"Error: {e}")
                    break
                    
        except Exception as e:
            logging.error(f"Traffic generation failed: {str(e)}")
            messagebox.showerror("Error", f"Traffic generation failed:\n{str(e)}")
        finally:
            self.running = False
            logging.info("Traffic stopped")

    def stop_traffic(self):
        """Stop the traffic generation"""
        self.running = False
        if self.device:
            try:
                usb.util.dispose_resources(self.device)
                logging.info("Disposed USB resources")
            except:
                logging.error("Failed to dispose USB resources")
                pass
        self.device = None
        logging.info("Traffic stopped")

# GUI Application
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Lumidigm USB Traffic Generator ({hex(LUMIDIGM_VID)}:{hex(LUMIDIGM_PID)})")
        self.geometry("400x200")
        self.resizable(False, False)
        
        self.generator = USBTrafficGenerator()
        
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        logging.info("GUI initialized")
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Device info
        info_frame = ttk.LabelFrame(main_frame, text="Device Info", padding="5")
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text=f"Vendor ID: {hex(LUMIDIGM_VID)}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Product ID: {hex(LUMIDIGM_PID)}").pack(anchor=tk.W)
        
        # Control buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="Start Traffic", command=self.start_traffic)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Stop Traffic", command=self.stop_traffic, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, text="Ready", foreground="blue")
        self.status_label.pack(anchor=tk.W)
        
        # Statistics
        stats_frame = ttk.Frame(status_frame)
        stats_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(stats_frame, text="Packets:").pack(side=tk.LEFT)
        self.packet_label = ttk.Label(stats_frame, text="0")
        self.packet_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(stats_frame, text="Bytes:").pack(side=tk.LEFT)
        self.byte_label = ttk.Label(stats_frame, text="0")
        self.byte_label.pack(side=tk.LEFT, padx=5)
        
        self.update_status()
        logging.info("UI setup complete")
        
    def update_status(self):
        if self.generator.running:
            self.status_label.config(text="Running", foreground="green")
        else:
            self.status_label.config(text="Ready", foreground="blue")
            
        self.packet_label.config(text=str(self.generator.packet_count))
        self.byte_label.config(text=str(self.generator.byte_count))
        
        # Schedule the next update
        self.after(100, self.update_status)
        logging.debug("Status updated")
        
    def start_traffic(self):
        logging.info("Starting traffic")
        if self.generator.find_device():
            self.generator.running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.generator.traffic_thread = threading.Thread(target=self.generator.generate_traffic)
            self.generator.traffic_thread.daemon = True
            self.generator.traffic_thread.start()
            
    def stop_traffic(self):
        logging.info("Stopping traffic")
        self.generator.stop_traffic()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
    def on_close(self):
        logging.info("Closing application")
        self.generator.stop_traffic()
        self.destroy()

# Main entry point
if __name__ == "__main__":
    logging.info("Starting application")
    app = App()
    app.mainloop()
    logging.info("Application exited")