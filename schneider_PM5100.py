#!/usr/bin/env python3
# Copyright 2024 Arup
# MIT License

# Reads kwh register from Schneider PM5100 series modbus electricity meter
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
import json
import serial.tools.list_ports

BAUDRATE = 9600

PM5100_REGISTER_MAP = {
    "manufacturer_label":                                        (70, 20, 'STRING40'),
    "product_label":                                             (30, 20, 'STRING40'),
    "serial_number_label":                                       (130, 2, 'INT32U'),
    "firmware_version_status":                                   (1638, 4, 'FIRMWARE'), # 3 registers 'A.B.C'
    "line1_neutral_voltage_sensor":                              (3028, 2, 'FLOAT32'),
    "line2_neutral_voltage_sensor":                              (3030, 2, 'FLOAT32'),
    "line3_neutral_voltage_sensor":                              (3032, 2, 'FLOAT32'),
    "average_neutral_voltage_sensor":                            (3028, 2, 'FLOAT32'),
    "line1_line2_voltage_sensor":                                (3020, 2, 'FLOAT32'),
    "line2_line3_voltage_sensor":                                (3022, 2, 'FLOAT32'),
    "line3_line1_voltage_sensor":                                (3024, 2, 'FLOAT32'),
    "average_line_voltage_sensor":                               (3026, 2, 'FLOAT32'),
    "line1_current_sensor":                                      (3000, 2, 'FLOAT32'),
    "line2_current_sensor":                                      (3002, 2, 'FLOAT32'),
    "line3_current_sensor":                                      (3004, 2, 'FLOAT32'),
    "neutral_current_sensor":                                    (3006, 2, 'FLOAT32'),
    "average_line_current_sensor":                               (3010, 2, 'FLOAT32'),
    "line1_neutral_power_sensor":                                (3054, 2, 'FLOAT32'),
    "line2_neutral_power_sensor":                                (3056, 2, 'FLOAT32'),
    "line3_neutral_power_sensor":                                (3058, 2, 'FLOAT32'),
    "total_power_sensor":                                        (3060, 2, 'FLOAT32'),
    "line1_neutral_apparent_power_sensor":                       (3070, 2, 'FLOAT32'),
    "line2_neutral_apparent_power_sensor":                       (3072, 2, 'FLOAT32'),
    "line3_neutral_apparent_power_sensor":                       (3074, 2, 'FLOAT32'),
    "total_apparent_power_sensor":                               (3076, 2, 'FLOAT32'),
    "line1_neutral_reactive_power_sensor":                       (3062, 2, 'FLOAT32'),
    "line2_neutral_reactive_power_sensor":                       (3064, 2, 'FLOAT32'),
    "line3_neutral_reactive_power_sensor":                       (3066, 2, 'FLOAT32'),
    "total_reactive_power_sensor":                               (3068, 2, 'FLOAT32'),
    "total_power_factor_sensor":                                 (3084, 2, 'PF4Q'),
    "total_energy_accumulator":                                  (3204, 4, 'INT64U'),
    "total_reactive_energy_accumulator":                         (3220, 4, 'INT64U'),
    "frequency_sensor":                                          (3110, 2, 'FLOAT32'),
    "line1_neutral_harmonic_distortion_voltage_sensor":          (21330, 2, 'FLOAT32'),
    "line2_neutral_harmonic_distortion_voltage_sensor":          (21332, 2, 'FLOAT32'),
    "line3_neutral_harmonic_distortion_voltage_sensor":          (21334, 2, 'FLOAT32'),
    "average_line_neutral_harmonic_distortion_voltage_sensor":   (21338, 2, 'FLOAT32'),
    "line1_harmonic_distortion_current_sensor":                  (21300, 2, 'FLOAT32'),
    "line2_harmonic_distortion_current_sensor":                  (21302, 2, 'FLOAT32'),
    "line3_harmonic_distortion_current_sensor":                  (21304, 2, 'FLOAT32'),
    "neutral_harmonic_distortion_current_sensor":                (21306, 2, 'FLOAT32')
}


def pf_from_pf4q(pf4q):
    """Schneider meters encode directionality of real and reactive power in 4 quadrant form"""
    # NaN special case
    if pf4q != pf4q:
        pf = 1.0
    # quadrant II, negative real power, positive reactive power
    elif pf4q < -1.0:
        pf = pf4q + 1.0
    # quadrant IV, positive real power, negative reactive power
    elif pf4q > 1.0:
        pf = pf4q - 1.0
    # quadrant I, positive real power, positive reactive power
    # quadrant III, negative real power, negative reactive power
    else:
        pf = pf4q
    return pf


def get_reading(instrument, register, decoder):
    reg_addr = register - 1
    if decoder == 'FLOAT32':
        output = instrument.read_float(reg_addr)  
    elif decoder == 'INT16U':
        output = instrument.read_register(reg_addr)  
    elif decoder == 'INT32U':
        vs = instrument.read_registers(reg_addr, 2)  
        output = (vs[0] << 16) + vs[1]
    elif decoder == 'INT64U':
        vs = instrument.read_registers(reg_addr, 4)  
        output = (vs[0] << 48) + (vs[1] << 32) + (vs[2] << 16) + vs[3]
    elif decoder == 'FIRMWARE':
        vs = instrument.read_registers(reg_addr, 4)
        output = f'{vs[0]}.{vs[1]}.{vs[2]}' 
    elif decoder[:6] == 'STRING':
        length = int(decoder[6:])
        output = instrument.read_string(reg_addr, length//2)  # 2 characters per register
        output = output.split('\x00',1)[0]       # drop everything after the first \x00 character
    elif decoder == 'PF4Q':
        output = pf_from_pf4q(instrument.read_float(reg_addr))
    else:
        sys.stderr.write(f"No implementation for {decoder}.\n")
        output = 0.0
    return output 


def get_readings(instrument, register_map):
    result = { k:get_reading(instrument, register, decoder) \
                   for k in register_map.keys() \
                       for register, length, decoder in [register_map[k]] }
    # apply timestamp
    result['timestamp'] = datetime.datetime.utcnow().isoformat('T')+'Z'
    return result


# on Ubuntu/Raspberry Pi, serial ports are in the form '/dev/ttyUSBx' where x is an integer 0-7
# on Windows, serial ports are in the form 'COMx' where x is an integer 1-8
def find_serial_device():
    ports = serial.tools.list_ports.comports()
    port_name = ''
    for port in ports:
        if port.device[0:11] == '/dev/ttyUSB' or port.device[0:3] == 'COM':
            port_name = port.device
            break
    if port_name == '':
        sys.stderr.write("Couldn't find serial device.\n")
        raise ConnectionError('Modbus error')
    return port_name
 

        
def configure(port):
    try:
        instrument = minimalmodbus.Instrument(port, 1, mode='rtu')
        instrument.serial.baudrate = BAUDRATE
        instrument.serial.bytesize = 8
        instrument.serial.stopbits = 1
        instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
        instrument.serial.timeout = 0.5
        return instrument
    except:
        sys.stderr.write(f'Failed to configure modbus on port {port}.\n')
        raise ConnectionError('Modbus error')


def print_all_readings(readings, as_json=False):
    # filter readings to remove 'NaN' values (eg single phase application)
    filtered_readings = { k:readings[k] for k in readings.keys() if readings[k] == readings[k] }
    if as_json:
        print(json.dumps(filtered_readings, sort_keys=False, indent=4))
    else:
        for k in filtered_readings.keys():
            print(f'{k:60}: {readings[k]}')


# starts here
try:
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        output_json = True
    else:
        output_json = False
    register_map = PM5100_REGISTER_MAP
    port = find_serial_device()
    print(f'Connecting to Modbus serial on port {port}.')
    instrument = configure(port)
    readings = get_readings(instrument, register_map)
    print_all_readings(readings, output_json)

except ConnectionError:
    sys.stderr.write('Error communicating with hardware.\n')
    sys.exit(1)



        



