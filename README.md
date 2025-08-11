# ESP32 DataFlasher

A Python GUI application to easily create and flash a SPIFFS filesystem to an ESP32 board.

## Features

- Graphical interface for generating and flashing SPIFFS binaries.
- Select COM port from a dropdown.
- Choose data folder via a file picker.
- Editable partition size (hex or decimal).
- Editable flash offset (hex or decimal).
- Configurable paths for spiffsgen.py and esptool.
- Live log output of the underlying commands.

## Prerequisites

- Python (recommended: Python 3.8+)
- Install pyserial for COM port detection:
  pip install pyserial
- Install esptool:
  pip install esptool

## Usage

1. Prepare your data folder
   - Create a folder named data (or any folder you prefer) and put your files inside.
   - Keep the total size within your SPIFFS partition limit.

2. Launch the application
   python "ESP32 DataFlasher.py"

3. Configure settings in the GUI
   - COM Port → Select your ESP32 serial port.
   - Partition size → e.g., 0x6A000 (must match your partition table).
   - Flash offset → e.g., 0x16000 (must match your partition table).
   - Data folder → Click Browse to pick your folder.
   - Optionally adjust spiffsgen.py and esptool paths.

4. Generate SPIFFS binary
   - Click Generate SPIFFS — this runs:
     python spiffsgen.py <partition_size> <data_folder> <output_file>
     Example:
     python spiffsgen.py 0x6A000 data spiffs.bin

5. Flash to ESP32
   - Click Flash to ESP32 — this runs:
     esptool --chip esp32c6 --port <COM_PORT> write_flash <offset> <output_file>
     Example:
     esptool --chip esp32c6 --port COM8 write_flash 0x16000 spiffs.bin

## Notes

- The partition size and offset must match your ESP32’s partition table.
- If you see a "SpiffsFullError: the image size has been exceeded", either:
  - Increase the partition size (and update your partition table accordingly), or
  - Reduce the amount of data in your folder.
- The GUI logs all commands so you can see exactly what’s being run.

## Example Workflow

1. Install dependencies:
   pip install pyserial esptool
2. Place files in your data folder.
3. Run:
   python "ESP32 DataFlasher.py"
4. Select COM port, set partition size & offset, choose the data folder.
5. Click Generate SPIFFS.
6. Click Flash to ESP32.
