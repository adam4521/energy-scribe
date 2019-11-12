#! /usr/bin/env python3
# For raspberry pi with blinkt led accessory

# number patterns:
# 0                     ...**...  blue
# 1			.......*  blue
# 2                     ......**  blue
# 3                     .....***  blue
# 4                     ....****  blue
# 5                     ...*****  blue
# 6                     ..******  blue
# 7                     .*******  blue
# 8                     ********  blue
# 9                     ***..***  blue
# dot                   *......*  white

import blinkt
import sys
import time
import socket

colours = { 'red': (200,0,0), 'green': (0,200,0), 'blue': (0,0,200), 'yellow': (200,200,0),\
        'cyan': (0,200,200), 'magenta': (200,0,200), 'white': (200,200,200), 'off': (0,0,0) }


def display_number(number):
    try:
        col = colours['blue']
        if number == 9:
            for i in range(0, 3):
                blinkt.set_pixel(i, col[0], col[1], col[2])
            for i in range(5, 8):
                blinkt.set_pixel(i, col[0], col[1], col[2])
        elif number == 0:
            for i in range(3, 5):
                blinkt.set_pixel(i, col[0], col[1], col[2])
        else:
            for i in range(0, number):
                blinkt.set_pixel(i, col[0], col[1], col[2])
        blinkt.show()
    except:
        sys.stderr.write('Colour or pixel not recognised.\n')
        sys.exit(1)

def display_dot():
    try:
        col = colours['white']
        blinkt.set_pixel(0, col[0], col[1], col[2])
        blinkt.set_pixel(7, col[0], col[1], col[2])
        blinkt.show()
    except:
        sys.stderr.write('Colour or pixel not recognised.\n')
        sys.exit(1)

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


blinkt.set_clear_on_exit(False)
blinkt.clear()
blinkt.show()
try:
    for char in get_ip():
        if char == '.':
            display_dot()
            time.sleep(3)
        else: 
            display_number(int(char))
            time.sleep(2)
        blinkt.clear()
        blinkt.show()

except:
    sys.stderr.write('Character in string not recognised.\n')
    sys.exit(1)

