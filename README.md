# ESP32DataFlasher

A console application to save data as SPIFFS on an ESP32 board.

## Prerequisites

- Python (recommended: Python 3.8+)
- `esptool` and `spiffsgen.py` must be installed via pip:
  ```bash
  pip install esptool
  ```
- Download `spiffsgen.py` from the [Espressif SPIFFS documentation](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/storage/spiffs.html).

## Usage

### 1. Prepare Data

- Place the files you want to flash into the `data` directory.

### 2. Generate SPIFFS Binary

- Open a terminal in the same directory as `spiffsgen.py`.
- Run the following command to generate the SPIFFS binary:
  ```bash
  python spiffsgen.py 0x30000 data spiffs.bin
  ```
  - `0x30000` is the available partition size (adjust as needed).
  - `data` is the folder containing your files.
  - `spiffs.bin` is the output binary file.

### 3. Flash SPIFFS Binary to ESP32

- Connect your ESP32 board via USB.
- Use `esptool` to write the SPIFFS binary to the device:
  ```bash
  esptool --chip esp32c6 --port COM8 write_flash 0x16000 spiffs.bin
  ```
  - Replace `COM8` with your actual serial port.
  - `0x16000` is the offset according to your partition table for SPIFFS storage.

## Notes

- The offset (`0x16000`) must match the SPIFFS partition offset in your ESP32 partition table.
- For more details, refer to the [Espressif SPIFFS documentation](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/storage/spiffs.html).

## Example Workflow

1. Install dependencies:
   ```bash
   pip install esptool
   ```
2. Prepare your files in the `data` folder.
3. Generate the SPIFFS binary:
   ```bash
   python spiffsgen.py 0x30000 data spiffs.bin
   ```
4. Flash to ESP32:
   ```bash
   esptool --chip esp32c6 --port COM8 write_flash 0x16000 spiffs.bin
   ```


