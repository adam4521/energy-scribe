# energy-scribe
## kwh meter reading and logging

Target device is Raspberry Pi version 2 or later.
Electrical meter with serial or modbus ad2apter is connected to RaPi.
Uses RaPi blinkt LED hardware shield for "running status" display.
The project consists of the following files:

### `auto.sh`
A script that should be configured to auto start on power up. Displays IP address on the blinkt display twice and then calls the `continuous_read.py` program.
Script will restart if the continuous_read.py program terminates.

### `continuous_read.py`
Provides a timed loop to read from meter(s) and write values to USB stick.
Indicates status/health on LED blinkt shield.
Calls a sub-process to actually acquire the readings, collecting from stdout.
Edit this file to point to a different acquisition program or to change the path for data logging.
Default is to log data to a new CSV file in a kwhmeter folder on a USB stick.
Will recover and reconnect if there is an interruption to the serial interface.
Will exit with error 1 if the USB stick is detached or path not found.

Status LEDs:
* 0 Purple: program is running, Red: program halted
* 1 Green: acquisition running, Red: acquisition failed
* 2 Blue: log writing, Red: log writing failed.

### `blinkt_display_ip_address.py`
Reads out the device IP address as a succession of coloured LED codes.
* 0 = two blue LEDs, centred.
* 1-8 = one to eight blue LEDs.
* 9 = Three blue leds, gap, three blue leds.
* DOT = Two white leds.

### `blinkt_indicator.py`
Test the blinkt hardware.

### `current_cost.py`
Read one line of power values (W) from up to nine wireless current cost meters connected to the base station.
Writes vaules to `stdout` as CSV text with timestamp.

### `hiking_dds238_2.py`
Read one line of electrical values (V, A, W, VAR, pf, freq, kWh) from the Hiking DDS238-2 modbus meter. Write values to `stdout` as CSV text with timestamp.



