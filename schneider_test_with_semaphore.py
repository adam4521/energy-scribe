#!/usr/bin/env python3
# Copyright 2021 Arup
# MIT License

import minimalmodbus
import serial
#import os
import sys
import posix_ipc as px

PORT = '/dev/ttyUSB0'
BAUDRATE = 9600
TIMEOUT = 2    # wait for rs485_semaphore lock for up to 2 seconds

def get_readings():
    instrument = minimalmodbus.Instrument(PORT, 1)
    instrument.serial.baudrate = BAUDRATE
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




# starts here
# the semaphore code allows communication with other process(es) so that they can
# use the RS485 bus without collision.

try:
    # get a connection to an existing operating system semaphore called "/rs485"
    # or create a new one if it doesn't already exist.
    rs485_semaphore = px.Semaphore("/rs485", flags=px.O_CREAT, initial_value=1)

    # while we are using the serial bus, decrement the semaphore
    # this function will block and wait if semaphore value=0 already
    rs485_semaphore.acquire(TIMEOUT)

    # we're clear to proceed: operate the RS485 bus
    get_readings()

    # we're done, increment and close the semaphore object.
    rs485_semaphore.release()
    rs485_semaphore.close()

except px.BusyError:
    # if we reach here the .acquire() function blocked for longer than
    # TIMEOUT indicating another process failed to clear the semaphore
    # quickly and may be deadlocked or hanging. The .unlink() will dispose
    # of the underlying semaphore on the system and allow a fresh semaphore
    # IPC object to be created next time. This will allow error recovery but
    # you must check for stuck processes and underlying cause if you see
    # this error.
    sys.stderr.write("RS485 semaphore stayed busy for too long: unlinking.\n")
    rs485_semaphore.unlink()
    rs485_semaphore.close()
    sys.exit(1)

except:
    # if we reach here we likely have had an I/O error on the serial port.
    sys.stderr.write("System error: probably serial port IO.\n")
    rs485_semaphore.release()
    rs485_semaphore.close()
    sys.exit(1)


