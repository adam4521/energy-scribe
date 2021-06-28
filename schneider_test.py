#!/usr/bin/env python3
import minimalmodbus
import serial
import os
import sys
import time
import glob

semaphore = '/dev/shm/rs485.pid' + str(os.getpid()) + '.wants-it'

def raise_semaphore():
    try:
        open(semaphore, 'w').close()
        os.utime(semaphore, None)
    except:
        sys.stderr.write("Couldn't raise semaphore.\n")

def clear_semaphore():
    try:
        os.unlink(semaphore)
    except:
        sys.stderr.write("Couldn't clear semaphore.\n")

def check_semaphores():
    return len(glob.glob('/dev/shm/rs485*'))

def clear_other_semaphores():
    for f in glob.glob('/dev/shm/rs485*'):
        if f != semaphore:
            os.unlink(f)

try:
    raise_semaphore()
    c = 0  # counter
    while check_semaphores() > 1:
        time.sleep(0.5)
        c = c + 1
        if c > 10:
            clear_other_semaphores()  # don't wait forever, clear blockers eventually

    instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1)
    instrument.serial.baudrate = 9600
    instrument.serial.parity = serial.PARITY_NONE
    instrument.serial.timeout = 0.5
    instrument.serial.stopbits = 1
    instrument.serial.bytesize = 8
    instrument.serial.timeout = 0.5
 

    print(instrument.read_string(29,20))
    print(instrument.read_string(49,20))
    print(instrument.read_string(69,20))
    print("Current: ", instrument.read_float(2999))
    print("Voltage: ", instrument.read_float(3027))
    print("Active Power: ", instrument.read_float(3053), "kW")
    print("Reactive Power: ", instrument.read_float(3067), "kVAR")
    print("Apparent Power: ", instrument.read_float(3075), "kVA")

    # need to process quadrant information in the datasheet
    pf = instrument.read_float(3083)
    if pf < 0:
        if pf < -1:
            print("Power factor: ", -2-pf, " leading")
        else:
            print("Power factor: ", pf, " lagging")
    else:
        if pf > 1:
            print("Power factor: ", 2-pf, " leading")
        else:
            print("Power factor: ", pf, " lagging")

    print("Cumulative active energy: ", instrument.read_float(45099), "Wh")
    print("Cumulative reactive energy: ", instrument.read_float(45101), "VARh")

    clear_semaphore()


except:
    sys.stderr.write("Failed to operate the serial port.\n")
    clear_semaphore()
    exit(1)


