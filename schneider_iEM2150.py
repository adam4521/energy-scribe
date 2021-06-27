#!/usr/bin/env python3

# Reads kwh register from Schneider iEM2150 modbus electricity meter
# On Ubuntu and similar systems, the serial ports have root user permissions.
# To change this, add ordinary user to the 'dialout' security group.
# sudo usermod -a -G dialout $USER
# requires minimalmodbus library: sudo pip3 install minimalmodbus

import minimalmodbus
import datetime
import time
import sys
import os
import glob
import serial.tools.list_ports

# on Ubuntu, serial ports are in the form '/dev/ttyUSBx' where x is an integer 0-7
# on Windows, serial ports are in the form 'COMx' where x is an integer 1-8
def find_serial_device():
    ports = serial.tools.list_ports.comports()
    port_name = ''
    for port in ports:
        if port.device[0:11] == '/dev/ttyUSB' or port.device[0:3] == 'COM':
            port_name = port.device
            break
    if port_name == '':
        sys.stderr.write('Couldn\'t find serial device.\n')
        raise ConnectionError('Modbus error')
    return port_name
 

        
def configure(port):
    try:
        instrument = minimalmodbus.Instrument(port, 1, mode='rtu')
        instrument.serial.baudrate = 9600
        instrument.serial.bytesize = 8
        instrument.serial.stopbits = 1
        instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
        instrument.serial.timeout = 0.5
        return instrument
    except:
        sys.stderr.write('Failed to configure modbus on port ' + port + '\n')
        raise ConnectionError('Modbus error')

def get_timestamp():
    now = time.gmtime()
    return time.strftime('%Y/%m/%d %H:%M:%S', now)

def pf_adjust(pf_raw):
    if pf_raw < 0:
        if pf_raw < -1:
            return -2-pf_raw, "leading"
        else:
            return pf, "lagging"
    else:
        if pf_raw > 1:
            return 2-pf_raw, "leading"
        else:
            return pf, "lagging"

def get_readings(instrument):
    try:
        # resulting low level bus comms noted in comments
        volts = instrument.read_float(3027)
            # typically sends 01 03 0b d3 00 02 37 d6      addr(1) fn(1) start-reg(2) quant-reg(2) crc(2)
            # and receives    01 03 04 43 6f 97 0a 31 9d   addr(1) fn(1) quant-bytes(1) float(4) crc(2)
        amps = instrument.read_float(2999)
            # typically sends 01 03 0b b7 00 02 76 09
            # and receives    01 03 04 3c cc cc cd a2 c9
        power = instrument.read_float(3053)
            # typically sends 01 03 0b ed 00 02 56 1a
            # and receives    01 03 04 38 30 29 28 e8 d2
        reactive_power = instrument.read_float(3067)
            # typically sends 01 03 0b fb 00 02 b7 de
            # and receives    01 03 04 bb b0 96 35 70 87
        pf, pf_direction = pf_adjust(instrument.read_float(3083))
            # typically sends 01 03 0c 0b 00 02 b6 99
            # and receives    01 03 04 3f ff 00 69 06 39
        freq = instrument.read_float(3109)
            # typically sends 01 03 0c 25 00 02 d6 90
            # and receives    01 03 04 42 47 f2 b1 db 4a
        energy = instrument.read_float(45099)
            # typically sends 01 03 b0 2b 00 02 92 c3
            # and receives    01 03 04 43 2c d7 f7 30 08
        return volts, amps, power, reactive_power, pf, pf_direction, freq, energy
    except:
        sys.stderr.write('Failed to read instrument.\n')
        raise ConnectionError('Modbus error')

def print_csv_all_readings(instrument):
    try:
        volts, amps, power, reactive_power, pf, pf_direction, freq, energy = get_readings(instrument)
        output = '"' + str(get_timestamp()) +  '",' \
                 + str(volts) + ',' \
                 + str(amps) + ',' \
                 + str(power) + ',' \
                 + str(reactive_power) + ',' \
                 + str(pf) + ',' \
                 + '"' + pf_direction + '",' \
                 + str(freq) + ',' \
                 + str(energy) + '\n'
        sys.stdout.write(output)
    except:
        sys.stderr.write('Failed to read instrument or write output.\n')
        raise ConnectionError('Modbus or write error')


def print_json_all_readings(instrument):
    try:
        volts, amps, power, reactive_power, pf, pf_direction, freq, energy = get_readings(instrument)
        output = '{"version": 1, ' +\
                 '"timestamp": "' + get_timestamp() + '", ' +\
                 '"points": {"voltage": {"present_value": ' + volts + '}, ' +\
                 '"current": {"present_value": '            + amps + '}, ' +\
                 '"power": {"present_value": '              + power + '}, ' +\
                 '"reactive power": {"present_value": '     + reactive_power + '}, ' +\
                 '"power factor": {"present_value": '       + pf + '}, ' +\
                 '"power factor direction": {"present_value": ' + pf_direction + '}, ' +\
                 '"frequency": {"present_value": '          + freq + '}, ' +\
                 '"energy": {"present_value": '             + energy + '}}}\n'
        # only write the output if we have successfully acquired the payload
        sys.stdout.write(output)
    except:
        sys.stderr.write('Failed to complete read of instrument state.\n')
        raise ConnectionError('Modbus error')

def print_all_readings(instrument):
    try:
        volts, amps, power, reactive_power, pf, pf_direction, freq, energy = get_readings(instrument)
        output = volts + ' V\n' +\
                 amps + ' A\n' +\
                 power + ' W\n' +\
                 reactive_power + ' VAR\n' +\
                 pf + ' pf\n' +\
                 pf_direction + ' pf direction\n' +\
                 freq + ' Hz\n' +\
                 energy + ' kWh\n'
        sys.stdout.write(output)
    except:
        sys.stderr.write('Failed to complete read of instrument state.\n')
        raise ConnectionError('Modbus error')


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
    port = find_serial_device()
    raise_semaphore()
    c = 0  # counter
    while check_semaphores() > 1:
        time.sleep(0.5)
        c = c + 1
        if c > 10:
            clear_other_semaphores()  # don't wait forever, clear blockers eventually

    instrument = configure(port)
    print_csv_all_readings(instrument)
    clear_semaphore()

except ConnectionError:
    sys.stderr.write('Error communicating with hardware.\n')
    sys.exit(1)



        



