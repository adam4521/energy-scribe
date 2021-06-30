# energy-scribe
## kwh meter reading and logging

Target device is Raspberry Pi version 2 or later.
Electrical meter with serial or modbus adapter is connected to RaPi.
Uses RaPi blinkt LED hardware shield for status display.
Currently supports Current Cost CC128 energy monitor, Hiking DDS238-2 ZN/S single phase meter and Schneider iEM2150 single phase meter.
The project consists of the following files:

### `auto.sh`
A script that should be configured to auto start on power up. Displays IP address on the blinkt display twice and then calls the `continuous_read.py` program.
This script will restart itself if the continuous_read.py program terminates.

### `continuous_read.py`
Provides a timed loop to read from meter(s) and write values to USB stick.
Indicates running status/health on LED blinkt shield.
Calls a sub-process to actually acquire the readings, collecting from the sub-process `stdout`.
Edit this file to point to a different acquisition program or to change the path for data logging.
Default is to log data to a new CSV file in a kwhmeter folder on a USB stick.
Will recover and reconnect if there is a temporary interruption or disconnection of the serial interface.
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
Usage: `./blinkt_indicator.py 2 red` turns LED 2 red.
`./blinkt_indicator 2 off` turns LED 2 off.

### `schneider_iEM2150.py`
Read one line of electrical values (V, A, kW, kVAR, pf, pf_direction, freq, kWh) from the Schneider iEM2150 modbus meter. Write values to `stdout` as CSV text with timestamp.

### `current_cost.py`
Read one line of power values (W) from up to nine wireless current cost meters connected to the base station.
Writes vaules to `stdout` as CSV text with timestamp.

### `hiking_dds238_2.py`
Read one line of electrical values (V, A, W, VAR, pf, freq, kWh) from the Hiking DDS238-2 modbus meter. Write values to `stdout` as CSV text with timestamp.


The python tools have dependencies on the following libraries that need to be installed:
* blinkt            Operates the Blinkt LED shield that attaches to Raspberry Pi
* minimalmodbus     Modbus library on top of serial bus
* posix_ipc         Enables cooperative sharing of comms port between processes running in parallel ('semaphore' versions of acquisition programs)

