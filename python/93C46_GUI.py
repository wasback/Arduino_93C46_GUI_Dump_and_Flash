#!/usr/bin/env python3
# eeprom_gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import serial
import serial.tools.list_ports
import time
import os

BAUD = 115200
EEPROM_BYTES = 128

class EEPROMGUI:
    def __init__(self, root):
        self.root = root
        root.title("EEPROM GUI Tool")
        self.ser = None

        # Port selection
        self.port_label = ttk.Label(root, text="Serial Port:")
        self.port_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(root, textvariable=self.port_var, width=20)
        self.port_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.refresh_ports()

        self.refresh_btn = ttk.Button(root, text="Refresh", command=self.refresh_ports)
        self.refresh_btn.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.connect_btn = ttk.Button(root, text="Connect", command=self.connect)
        self.connect_btn.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Buttons
        self.btn_frame = ttk.Frame(root)
        self.btn_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=5)

        self.read_bin_btn = ttk.Button(self.btn_frame, text="Save BIN to file", command=self.read_bin)
        self.read_bin_btn.grid(row=0, column=0, padx=5, pady=5)

        self.read_hex_btn = ttk.Button(self.btn_frame, text="Read HEX", command=self.read_hex)
        self.read_hex_btn.grid(row=0, column=1, padx=5, pady=5)

        self.read_text_btn = ttk.Button(self.btn_frame, text="Read Text", command=self.read_text)
        self.read_text_btn.grid(row=0, column=2, padx=5, pady=5)

        self.flash_btn = ttk.Button(self.btn_frame, text="Flash Binary", command=self.flash_bin)
        self.flash_btn.grid(row=1, column=0, padx=5, pady=5)

        self.Clearing_btn = ttk.Button(self.btn_frame, text="Write 0xFF", command=self.write_ff)
        self.Clearing_btn.grid(row=1, column=1, padx=5, pady=5)

        # Output text
        self.output = scrolledtext.ScrolledText(root, width=80, height=25)
        self.output.grid(row=2, column=0, columnspan=4, padx=5, pady=5)
        self.append_text("EEPROM GUI ready.\n")

    def append_text(self, txt):
        self.output.insert(tk.END, txt + "\n")
        self.output.see(tk.END)
        self.root.update()

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)

    def connect(self):
        port = self.port_var.get()
        if not port:
            messagebox.showerror("Error", "Select a serial port first")
            return
        try:
            self.ser = serial.Serial(port, BAUD, timeout=2)
            self.append_text(f"Connecting to {port}...")
            time.sleep(1.0)
            # wait for banner
            start = time.time()
            while time.time() - start < 3.0:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    self.append_text(f"Arduino: {line}")
                    if "EEPROM Slave Ready" in line:
                        break
            while self.ser.in_waiting:
                self.ser.readline()
            self.append_text("Connected successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open port {port}: {e}")

    def read_bin(self):
        if not self.ser:
            messagebox.showerror("Error", "Not connected")
            return
        out_file = filedialog.asksaveasfilename(defaultextension=".bin", filetypes=[("Binary files", "*.bin")])
        if not out_file:
            return
        try:
            self.ser.write(b'READ_BIN\n')
            # wait for BEGIN_BIN
            start = time.time()
            while time.time() - start < 5.0:
                line = self.ser.readline()
                if not line:
                    continue
                line_str = line.decode('utf-8', errors='ignore').strip()
                if line_str.startswith("BEGIN_BIN"):
                    parts = line_str.split()
                    expected = int(parts[1])
                    break
            else:
                raise RuntimeError("Timeout waiting for BEGIN_BIN")

            data = b''
            remaining = expected
            while remaining:
                chunk = self.ser.read(remaining)
                if not chunk:
                    raise RuntimeError("Timeout receiving binary")
                data += chunk
                remaining -= len(chunk)

            # wait until END_BIN
            start = time.time()
            while time.time() - start < 2.0:
                line = self.ser.readline()
                if not line:
                    continue
                if line.decode('utf-8', errors='ignore').strip() == "END_BIN":
                    break

            # Save to file
            with open(out_file, "wb") as f:
                f.write(data)
            self.append_text(f"Binary dump saved to {out_file} ({len(data)} bytes)")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read binary: {e}")
    def read_hex(self):
        if not self.ser:
            messagebox.showerror("Error", "Not connected")
            return
        try:
            self.ser.write(b'READ_HEX\n')
            lines = []
            while True:
                line = self.ser.readline()
                if not line:
                    continue
                text = line.decode('utf-8', errors='replace').rstrip('\r\n')
                if text.strip() == "END_HEX":
                    break
                lines.append(text)
            self.append_text("HEX DUMP:\n" + "\n".join(lines))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read HEX: {e}")

    def read_text(self):
        if not self.ser:
            messagebox.showerror("Error", "Not connected")
            return
        try:
            self.ser.write(b'READ_TEXT\n')
            text_data = ''
            while True:
                line = self.ser.readline()
                if not line:
                    continue
                text = line.decode('utf-8', errors='replace').rstrip('\r\n')
                if text == "END_TEXT":
                    break
                if text == "BEGIN_TEXT":
                    continue
                text_data += text
            self.append_text("ASCII TEXT:\n" + text_data)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read text: {e}")

    def flash_bin(self):
        if not self.ser:
            messagebox.showerror("Error", "Not connected")
            return
        in_file = filedialog.askopenfilename(filetypes=[("Binary files", "*.bin")])
        if not in_file:
            return
        try:
            with open(in_file, "rb") as f:
                data = f.read()
            if len(data) > EEPROM_BYTES:
                self.append_text(f"Warning: file larger than {EEPROM_BYTES} bytes, truncating")
                data = data[:EEPROM_BYTES]
            self.ser.write(f"WRITE_BIN {len(data)}\n".encode('ascii'))
            # wait READY
            start = time.time()
            ready = False
            while time.time() - start < 5.0:
                line = self.ser.readline()
                if not line:
                    continue
                txt = line.decode('utf-8', errors='ignore').strip()
                if txt == "READY":
                    ready = True
                    break
            if not ready:
                raise RuntimeError("Device didn't respond READY")
            self.ser.write(data)
            time.sleep(0.05)
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("OK"):
                self.append_text(f"Flashed {in_file} successfully")
            else:
                self.append_text(f"Flashing failed: {line}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to flash binary: {e}")

    def write_ff(self):
        if not self.ser:
            messagebox.showerror("Error", "Not connected")
            return
        confirm = messagebox.askyesno("Confirm", "This will write 0xFF to entire EEPROM. Continue?")
        if not confirm:
            return
        data = bytes([0xFF]*EEPROM_BYTES)
        try:
            self.ser.write(f"WRITE_BIN {len(data)}\n".encode('ascii'))
            start = time.time()
            ready = False
            while time.time() - start < 5.0:
                line = self.ser.readline()
                if not line:
                    continue
                txt = line.decode('utf-8', errors='ignore').strip()
                if txt == "READY":
                    ready = True
                    break
            if not ready:
                raise RuntimeError("Device didn't respond READY")
            self.ser.write(data)
            time.sleep(0.05)
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("OK"):
                self.append_text("EEPROM Clearingd successfully (0xFF).")
            else:
                self.append_text(f"Clearing failed: {line}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write FF: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = EEPROMGUI(root)
    root.mainloop()
