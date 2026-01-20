"""
ESP32 SPIFFS & Flash GUI

Save this file as `esp32_spiffs_gui.py` and run with Python 3.8+.
Requires: pyserial
    pip install pyserial

This Tkinter GUI lets you:
 - pick a COM port (refreshable)
 - select an ESP32 chip type (esp32, esp32s2, esp32s3, esp32c3, esp32c6, esp32h2, esp8266)
 - choose a data folder to pack
 - set partition size and flash offset (hex or decimal)
 - optionally set paths to spiffsgen.py and esptool executable
 - generate the spiffs binary (runs `python spiffsgen.py <partsize> <data_folder> <outfile>`)
 - flash the resulting bin to an ESP32 via esptool

Notes:
 - The GUI spawns threads for long-running commands so the UI stays responsive.
 - Ensure `spiffsgen.py` and `esptool` are reachable or provide full paths.
 - On Windows, esptool is typically `esptool.exe` or `python -m esptool`.

"""

import os
import sys
import threading
import subprocess
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

try:
    import serial.tools.list_ports as list_ports
except Exception:
    list_ports = None

APP_TITLE = "ESP32 SPIFFS Generator & Flasher"
DEFAULT_OUTPUT = "spiffs.bin"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("760x520")
        self.resizable(True, True)
        self.create_widgets()

    def create_widgets(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(frm)
        left.pack(side=tk.TOP, fill=tk.X)

        # COM port selection
        port_row = ttk.Frame(left)
        port_row.pack(fill=tk.X, pady=4)
        ttk.Label(port_row, text="COM Port:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar()
        self.port_cb = ttk.Combobox(port_row, textvariable=self.port_var, width=18, state='readonly')
        self.port_cb.pack(side=tk.LEFT, padx=6)
        ttk.Button(port_row, text="Refresh", command=self.refresh_ports).pack(side=tk.LEFT)
        
        # ESP32 chip selection
        ttk.Label(port_row, text="Chip:").pack(side=tk.LEFT, padx=(10,0))
        self.chip_var = tk.StringVar(value="esp32c6")
        chip_options = ["esp32", "esp32s2", "esp32s3", "esp32c3", "esp32c6", "esp32h2", "esp8266"]
        self.chip_cb = ttk.Combobox(port_row, textvariable=self.chip_var, width=12, state='readonly', values=chip_options)
        self.chip_cb.pack(side=tk.LEFT, padx=6)

        # Partition size and offset
        po_row = ttk.Frame(left)
        po_row.pack(fill=tk.X, pady=4)
        ttk.Label(po_row, text="Partition size:").pack(side=tk.LEFT)
        self.part_var = tk.StringVar(value="0x6A000")
        self.part_entry = ttk.Entry(po_row, textvariable=self.part_var, width=16)
        self.part_entry.pack(side=tk.LEFT, padx=6)
        ttk.Label(po_row, text="Flash offset:").pack(side=tk.LEFT, padx=(10,0))
        self.off_var = tk.StringVar(value="0x16000")
        self.off_entry = ttk.Entry(po_row, textvariable=self.off_var, width=16)
        self.off_entry.pack(side=tk.LEFT, padx=6)

        # Data folder selection
        data_row = ttk.Frame(left)
        data_row.pack(fill=tk.X, pady=4)
        ttk.Label(data_row, text="Data folder:").pack(side=tk.LEFT)
        self.data_var = tk.StringVar()
        self.data_entry = ttk.Entry(data_row, textvariable=self.data_var, width=46)
        self.data_entry.pack(side=tk.LEFT, padx=6)
        ttk.Button(data_row, text="Browse", command=self.browse_data).pack(side=tk.LEFT)

        # spiffsgen and esptool paths
        tools_row = ttk.Frame(left)
        tools_row.pack(fill=tk.X, pady=6)
        ttk.Label(tools_row, text="spiffsgen (script or path):").pack(side=tk.LEFT)
        self.spiffsgen_var = tk.StringVar(value="spiffsgen.py")
        ttk.Entry(tools_row, textvariable=self.spiffsgen_var, width=30).pack(side=tk.LEFT, padx=6)
        ttk.Label(tools_row, text="esptool (exe or command):").pack(side=tk.LEFT, padx=(8,0))
        self.esptool_var = tk.StringVar(value="esptool")
        ttk.Entry(tools_row, textvariable=self.esptool_var, width=20).pack(side=tk.LEFT, padx=6)

        # Output filename
        out_row = ttk.Frame(left)
        out_row.pack(fill=tk.X, pady=4)
        ttk.Label(out_row, text="Output file:").pack(side=tk.LEFT)
        self.out_var = tk.StringVar(value=DEFAULT_OUTPUT)
        ttk.Entry(out_row, textvariable=self.out_var, width=36).pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(out_row, text="Overwrite", variable=tk.IntVar(value=1)).pack(side=tk.LEFT, padx=6)

        # Buttons
        btn_row = ttk.Frame(left)
        btn_row.pack(fill=tk.X, pady=8)
        ttk.Button(btn_row, text="Generate SPIFFS", command=self.generate_spiffs).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_row, text="Flash to ESP32", command=self.flash_image).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_row, text="Open output folder", command=self.open_output_folder).pack(side=tk.LEFT, padx=8)

        # Log area
        log_label = ttk.Label(frm, text="Log:")
        log_label.pack(anchor=tk.W, pady=(8,0))
        self.log = scrolledtext.ScrolledText(frm, height=18)
        self.log.pack(fill=tk.BOTH, expand=True, pady=(0,8))
        self.log.configure(state='disabled')

        # initial port refresh
        self.refresh_ports()

    def append_log(self, text):
        self.log.configure(state='normal')
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.configure(state='disabled')

    def refresh_ports(self):
        ports = []
        if list_ports is not None:
            try:
                ports = [p.device for p in list_ports.comports()]
            except Exception:
                ports = []
        # Fallback heuristic on posix/windows
        if not ports:
            if sys.platform.startswith('win'):
                # show COM1..COM20 as guess
                ports = [f"COM{i}" for i in range(1, 21)]
            else:
                ports = ['/dev/ttyUSB0', '/dev/ttyACM0']
        self.port_cb['values'] = ports
        if ports:
            # if current selection is empty or not in list, pick first
            cur = self.port_var.get()
            if cur not in ports:
                self.port_var.set(ports[0])

    def browse_data(self):
        folder = filedialog.askdirectory()
        if folder:
            self.data_var.set(folder)

    def open_output_folder(self):
        out = self.out_var.get() or DEFAULT_OUTPUT
        folder = os.path.abspath(os.path.dirname(out))
        if not os.path.isdir(folder):
            folder = os.getcwd()
        if sys.platform.startswith('win'):
            os.startfile(folder)
        elif sys.platform.startswith('darwin'):
            subprocess.Popen(['open', folder])
        else:
            subprocess.Popen(['xdg-open', folder])

    def _parse_size(self, s):
        s = s.strip()
        if not s:
            raise ValueError('Empty size')
        # allow 0x hex or decimal
        if s.lower().startswith('0x'):
            return int(s, 16)
        return int(s, 10)

    def _run_command_threaded(self, args, cwd=None):
        def run():
            try:
                self.append_log('> ' + ' '.join(args))
                proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, text=True)
                for line in proc.stdout:
                    self.append_log(line.rstrip())
                proc.wait()
                self.append_log(f'Process exited with {proc.returncode}')
            except FileNotFoundError as e:
                self.append_log(f'Command not found: {e}')
                messagebox.showerror('Command not found', str(e))
            except Exception as e:
                self.append_log(f'Error running command: {e}')
                messagebox.showerror('Error', str(e))

        t = threading.Thread(target=run, daemon=True)
        t.start()
        return t

    def generate_spiffs(self):
        data = self.data_var.get().strip()
        if not data or not os.path.isdir(data):
            messagebox.showerror('Invalid data folder', 'Please choose a valid data folder to pack.')
            return
        try:
            partsize = self.part_var.get().strip()
            # verify parse
            _ = self._parse_size(partsize)
        except Exception:
            messagebox.showerror('Invalid partition size', 'Enter partition size as hex (0x6A000) or decimal (196608).')
            return
        out = self.out_var.get().strip() or DEFAULT_OUTPUT

        spiffsgen = self.spiffsgen_var.get().strip() or 'spiffsgen.py'
        # Build command. Use python to run spiffsgen if it's a .py file
        cmd = []
        if spiffsgen.lower().endswith('.py'):
            python_exe = sys.executable or 'python'
            cmd = [python_exe, spiffsgen, partsize, data, out]
        else:
            # assume it's executable
            cmd = [spiffsgen, partsize, data, out]

        # Run threaded
        self.append_log(f'Starting SPIFFS generation -> {out}')
        self._run_command_threaded(cmd)

    def flash_image(self):
        port = self.port_var.get().strip()
        if not port:
            messagebox.showerror('No port selected', 'Please select a COM port.')
            return
        out = self.out_var.get().strip() or DEFAULT_OUTPUT
        if not os.path.isfile(out):
            messagebox.showerror('Missing output', f'Output file not found: {out}')
            return
        try:
            offset = self.off_var.get().strip()
            _ = self._parse_size(offset)
        except Exception:
            messagebox.showerror('Invalid offset', 'Enter flash offset as hex (0x16000) or decimal.')
            return

        chip = self.chip_var.get().strip() or 'esp32c6'
        esptool = self.esptool_var.get().strip() or 'esptool'
        # prefer direct esptool executable, but many people use python -m esptool
        cmd = None
        if shutil.which(esptool):
            # found in PATH
            cmd = [esptool, '--chip', chip, '--port', port, 'write_flash', offset, out]
        else:
            # try invoking as python -m esptool
            python_exe = sys.executable or 'python'
            cmd = [python_exe, '-m', esptool, '--chip', chip, '--port', port, 'write_flash', offset, out]

        self.append_log(f'Starting flash to {port} at {offset} using {esptool} for chip {chip}')
        self._run_command_threaded(cmd)


if __name__ == '__main__':
    app = App()
    app.mainloop()
