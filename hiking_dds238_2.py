#!/usr/bin/env python3

# Reads kwh register from Hiking DDS238-2 ZN/S modbus electricity meter
# On Ubuntu and similar systems, the serial ports have root user permissions.
# To change this, add ordinary user to the 'dialout' security group.
# sudo usermod -a -G dialout $USER
# requires minimalmodbus library: sudo pip3 install minimalmodbus

import minimalmodbus
import datetime
import time
import sys
import os
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

def print_csv_all_readings(instrument, port):
    try:
        # date,voltage,current,power,reactive power,power factor,frequency,cumulative energy
        output = '"' + get_timestamp() +  '",' +\
                read_modbus(instrument, 0x000c, port, 1) + ',' +\
                read_modbus(instrument, 0x000d, port, 2) + ',' +\
                read_modbus(instrument, 0x000e, port, 0) + ',' +\
                read_modbus(instrument, 0x000f, port, 0) + ',' +\
                read_modbus(instrument, 0x0010, port, 3) + ',' +\
                read_modbus(instrument, 0x0011, port, 2) + ',' +\
                read_modbus(instrument, 0x000a, port, 2, True) + '\n'
        sys.stdout.write(output)
    except:
        sys.stderr.write('Failed to read instrument or write output.\n')
        raise ConnectionError('Modbus or write error')


def print_json_all_readings(instrument, port):
    try:
        output = '{"version": 1, ' +\
                 '"timestamp": "' + get_timestamp() + '", ' +\
                 '"points": {"voltage": {"present_value": ' + read_modbus(instrument, 0x000c, port, 1) + '}, ' +\
                 '"current": {"present_value": '            + read_modbus(instrument, 0x000d, port, 2) + '}, ' +\
                 '"power": {"present_value": '              + read_modbus(instrument, 0x000e, port, 0) + '}, ' +\
                 '"reactive power": {"present_value": '     + read_modbus(instrument, 0x000f, port, 0) + '}, ' +\
                 '"power factor": {"present_value": '       + read_modbus(instrument, 0x0010, port, 3) + '}, ' +\
                 '"frequency": {"present_value": '          + read_modbus(instrument, 0x0011, port, 2) + '}, ' +\
                 '"energy": {"present_value": '             + read_modbus(instrument, 0x000a, port, 2, True) + '}}}\n'
        # only write the output if we have successfully acquired the payload
        sys.stdout.write(output)
    except:
        sys.stderr.write('Failed to complete read of instrument state.\n')
        raise ConnectionError('Modbus error')

def print_all_readings(instrument, port):
    try:
        output = read_modbus(instrument, 0x000c, port, 1) + ' V\n' +\
                 read_modbus(instrument, 0x000d, port, 2) + ' A\n' +\
                 read_modbus(instrument, 0x000e, port, 0) + ' W\n' +\
                 read_modbus(instrument, 0x000f, port, 0) + ' VAR\n' +\
                 read_modbus(instrument, 0x0010, port, 3) + ' pf\n' +\
                 read_modbus(instrument, 0x0011, port, 2) + ' Hz\n' +\
                 read_modbus(instrument, 0x000a, port, 2, True) + ' kWh\n'
        sys.stdout.write(output)
    except:
        sys.stderr.write('Failed to complete read of instrument state.\n')
        raise ConnectionError('Modbus error')

def read_modbus(instrument, register, port, decimals, longvalue=False):
    try:
        if longvalue == True:
            reading = float(instrument.read_long(register)) / (10 ** decimals)
        else:
            reading = float(instrument.read_register(register, decimals))
        return str.format('%.2f' % reading)
    except:
        sys.stderr.write('Failed to read from register ' + format(register, '#04x') + '\n')
        raise ConnectionError('Modbus error')

def write_modbus(instrument, register, *values):
    try:
        instrument.write_multiple_registers(register, values)
    except:
        sys.stderr.write('Failed to write to port ' + port + '\n')
        raise ConnectionError('Modbus error')

def set_baud_rate(speed, port):
    lookup = { 9600:0b00010001, 4800:0b00010010, 2400:0b000010011, 1200:0b00010100 }
    write_modbus(0x15, port, lookup[speed])


try:
    port = find_serial_device()
    instrument = configure(port)
    print_csv_all_readings(instrument, port)

except ConnectionError:
    sys.stderr.write('Error communicating with hardware.\n')
    sys.exit(1)


        



