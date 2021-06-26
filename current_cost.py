#!/usr/bin/env python3
# Read from currentcost serial interface
# requires serial library: sudo pip3 install pyserial

import serial
import re
import sys
import csv
import time


def get_timestamp():
    now = time.gmtime()
    return time.strftime('%Y/%m/%d %H:%M:%S', now)


try:
    meter = serial.Serial('/dev/ttyUSB0', 57600)
    readings = [None] * 10
    csv_output = csv.writer(sys.stdout, quoting=csv.QUOTE_NONNUMERIC)
    while True:
        meter_reading = meter.readline().decode('utf-8')
        name_match = re.search(r"<sensor>(\d)</sensor>", meter_reading)
        if name_match:
            name = int(name_match.group(1))
        watts_match = re.search(r"<watts>(\d+)</watts>", meter_reading)
        if watts_match:
            watts = int(watts_match.group(1))
        if readings[name] != None:
            # break if the element is already populated
            break
        else:
            readings[name] = watts
    readings[0] = get_timestamp()
    csv_output.writerow(readings)

except:
    sys.stdout.flush()
    sys.stderr.write("Couldn't read from serial interface.\n")
    sys.exit(1)




