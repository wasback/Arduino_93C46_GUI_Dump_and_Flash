# 93C46 Library for Arduino

**Note:** This library works in 8-bit (128×8) or 16-bit (64×16) mode depending on ORG pin and the mode set via `set_mode()`. The examples below assume 8-bit (128 bytes) unless stated otherwise.

## Introduction

The 93C46 is a 1Kb EEPROM communicating over 3-wire serial (plus CS). This library implements bit-banged SPI-like access for reading and writing the chip. In addition to the Arduino-side library and examples, this repository now includes a **Python GUI tool** for reading, viewing, saving and flashing EEPROM images.

## New: Python GUI Tool

A cross-platform `Tkinter` GUI (`eeprom_gui.py`) is provided to interact with the Arduino slave sketch:

Features
- Scan and pick serial port (port scanner)
- Connect / disconnect to Arduino
- Read raw binary dump and **save to .bin**
- Read hex dump and show 8 lines × 16 bytes (128 bytes total)
- Read printable ASCII text extracted from EEPROM
- Flash a binary file to EEPROM (with size check and truncation to 128 bytes)
- Virginize EEPROM: write `0xFF` to the entire EEPROM
- Status and output log window
- Simple, robust handshake with the Arduino slave (waits for `EEPROM Slave Ready`)

### Requirements

- Python 3.x
- PySerial
- Tkinter (usually included with Python)
- The Arduino sketch `EEPROM_slave_fixed.ino` (or your own sketch that follows the same serial protocol)

### Protocol between Arduino and GUI

Commands (newline-terminated, ASCII):
- `READ_BIN` → Arduino replies `BEGIN_BIN <N>\n` then sends N raw bytes, then `END_BIN\n`
- `READ_HEX` → Arduino replies `BEGIN_HEX\n` then sends textual hex dump lines, then `END_HEX\n`
- `READ_TEXT` → Arduino replies `BEGIN_TEXT\n` then sends printable text then `END_TEXT\n`
- `WRITE_BIN <N>` → Arduino replies `READY\n`, GUI sends N raw bytes, Arduino replies `OK <checksum>\n` or `ERR <msg>\n`

### Using the GUI

1. Plug your Arduino and upload the Arduino slave sketch (the sketch prints `EEPROM Slave Ready` when ready).
2. Run the GUI: `python eeprom_gui.py`
3. Select the serial port from the dropdown, click **Connect**.
4. Use buttons to read/save hex/text or flash a `.bin` file. Use **Write 0xFF** to virginize the chip.

## Example: Save dump to file (binary)

Click **Read Binary** → file dialog appears → choose `dump.bin` to save the raw 128 bytes.

## Notes & Limitations

- The Arduino sketch included assumes 8-bit organization (128 bytes). If you use 16-bit organization, adjust both the Arduino sketch (word handling) and GUI expectations.
- The GUI relies on the Arduino slave protocol. Do not open the same serial port in another application during transfers.
- The library supports `ew_enable()`/`ew_disable()` for write protection. The Arduino sketch uses `ew_enable()` before writes and `ew_disable()` after writing.

## Files added/modified

- `EEPROM_slave_fixed.ino` — Arduino slave sketch implementing the serial protocol.
- `interactive_eeprom_ports.py` / `eeprom_gui.py` — interactive CLI and GUI tools for interacting with the EEPROM.
- `standalone_eeprom_safe.py` — standalone scripts for scripted usage.

