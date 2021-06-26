#!/usr/bin/env python3
import minimalmodbus
import serial


ser=serial.Serial('/dev/ttyUSB0')
print(ser.name)


instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1)
instrument.serial.baudrate = 9600
instrument.serial.timeout = 0.5
#value = instrument.read_float(3054,3,2)
#value = instrument.read_string(70,32,3)
value = instrument.read_register(130,2,3)
instrument.serial.timeout = 0.5
print(value)
