#!/bin/bash

# wait to make sure usb stick is automounted
sleep 10

# make the directory of this script the current working directory
cd "$(dirname "${BASH_SOURCE[0]}")"

# display the ip address on led pixel strip, twice
./blinkt_display_ip_address.py
sleep 2
./blinkt_display_ip_address.py

# now start the kwh meter logging 
./continuous_read.py

# if an error occurred causing the script to exit, attempt a restart
>&2 echo Attempting restart of auto.sh in 10 seconds...  
sleep 10
exec ./auto.sh


