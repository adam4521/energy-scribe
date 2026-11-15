#!/usr/bin/env python

# Custom udev rules are required to recognise the USB identifiers of the GW-Instek GDM-8042 multimeter.
# These rules are NOT NEEDED for the GDM-9041 multimeter.
#
# Proceed as follows:
# 1. Edit the rule file:
# sudo nano /etc/udev/rules.d/10-force-serial.rules
#
# 2. Enter the parameters for the GDM-8342 multimeter:
# SUBSYSTEM=="usb", ATTRS{idVendor}=="2184", ATTRS{idProduct}=="003d", MODE="0666", GROUP="dialout", RUN+="/sbin/modprobe cp210x", RUN+="/bin/sh -c 'echo 2184 003d > /sys/bus/usb-serial/drivers/cp210x/new_id'"
# [ In the event that custom rules are required for GDM-9041, the idVendor is 0x2184 and the idProduct is 0x008d]
#
# 3. Restart the sub-system:
# sudo udevadm control --reload-rules
# sudo udevadm trigger
#
# 4. Add the user account or service account to the dialout group
# sudo usermod -aG dialout $USER
#
# *********** WORK IN PROGRESS *************

import serial
import time


def identify_gdm_meter(port_path="/dev/ttyACM0"):
    print(f"Testing port {port_path} for GW-Instek multimeter...")
    
    try:
        # Open port with a strict timeout to prevent blocking indefinitely
        # GDM-9041 defaults to 8N1 (8 data bits, no parity, 1 stop bit)
        ser = serial.Serial(
            port=port_path,
            baudrate=115200,   # Set to match what is configured in your DMM Menu
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.5        # Crucial for scanning 
        )
        
        # 1. Clear any junk left over in the input/output buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # 2. Send the standard identification query terminated with a line feed
        ser.write(b"*IDN?\n")
        
        # 3. Read the line response back from the instrument
        response = ser.readline().decode('utf-8').strip()
        
        ser.close()
        
        # 4. Parse response to see if it belongs to your meter
        if "GWInstek" in response and "GDM9041" in response:
            print(f"✅ Success! Found GDM-9041 on {port_path}")
            print(f"Device Identity: {response}")
            return True
        elif "GWInstek" in response and "GDM8342" in response:
            print(f"✅ Success! Found GDM-8342 on {port_path}")
            print(f"Device Identity: {response}")
            return True
        else:
            print(f"❌ Device on {port_path} responded, but it is not the GDM-8342 or GDM-9041.")
            print(f"Received: {repr(response)}")
            return False
            
    except serial.SerialException as e:
        print(f"⚠️ Could not open or communicate with port {port_path}: {e}")
        return False



def setup_and_poll_meter(port_path="/dev/ttyACM0"):
    try:
        # Open connection (GDM-9041 USBCDC default protocol: 8N1)
        ser = serial.Serial(
            port=port_path,
            baudrate=115200, 
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2.0
        )
        
        print("Initializing meter...")
        ser.write(b"*RST\n")
        time.sleep(0.5) # Allow hardware a moment to reset nodes
        
        # Configure Primary - 1000V DC
        ser.write(b'SENS:FUNC "VOLT:DC"\n')
        ser.write(b'SENS:VOLT:DC:RANG 1000\n')
        
        # Configure Secondary - 500mA DC (0.5A)
        ser.write(b'SENS2:FUNC "CURR:DC"\n')
        ser.write(b'SENS2:CURR:DC:RANG 0.5\n')
        time.sleep(0.5) # Allow internal ADC loops to sync up
        
        print("Setup complete. Starting loop at 5-second intervals. Press Ctrl+C to stop.\n")
        
        while True:
            # Clear internal buffers to guarantee fresh data
            ser.reset_input_buffer()
            
            # Query dual values
            ser.write(b"VAL2?\n")
            raw_data = ser.readline().decode('utf-8').strip()
            
            if raw_data:
                try:
                    # Split the dual values
                    volt_raw, curr_raw = raw_data.split(',')
                    
                    voltage = float(volt_raw)
                    current = float(curr_raw) * 1000 # Convert Amps to mA for readable logs
                    
                    print(f"[{time.strftime('%X')}] Voltage: {voltage:7.2f} V | Current: {current:7.2f} mA")
                except ValueError:
                    print(f"Parsing error. Raw payload received: {raw_data}")
            else:
                print("Timeout: No data returned from meter.")
                
            time.sleep(5.0)
            
    except serial.SerialException as e:
        print(f"Serial communications failure: {e}")
    except KeyboardInterrupt:
        print("\nPolling stopped by user.")
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    if identify_gdm_meter("/dev/ttyACM0"):
        setup_and_poll_meter()




 
