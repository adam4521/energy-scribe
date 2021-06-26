#!/usr/bin/env python3
import minimalmodbus
import serial


ser=serial.Serial('/dev/ttyUSB0')
print(ser.name)


instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1)
instrument.serial.baudrate = 9600
instrument.serial.parity = serial.PARITY_NONE
instrument.serial.timeout = 0.5
instrument.serial.stopbits = 1
instrument.serial.bytesize = 8
instrument.serial.timeout = 0.5
information1 = instrument.read_string(29,20)
information2 = instrument.read_string(49,20)
information3 = instrument.read_string(69,20)
print(information1)
print(information2)
print(information3)


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


