#! /usr/bin/env python3
# For raspberry pi with blinkt led accessory
# Usage: 
# blinkt-indicator.py 2 red                  to light 3rd pixel (numbered 0 to 7)
# blinkt-indicator.py 2 off                  to extinguish 3rd pixel


import blinkt
import sys


colours = { 'red': (200,0,0), 'green': (0,200,0), 'blue': (0,0,200), 'yellow': (200,200,0),\
        'cyan': (0,200,200), 'magenta': (200,0,200), 'white': (200,200,200), 'off': (0,0,0) }


try:
    col = colours[sys.argv[2]]
    blinkt.set_clear_on_exit(False)
    blinkt.set_pixel(int(sys.argv[1]), col[0], col[1], col[2])
    blinkt.show()
except:
    sys.stderr.write('Colour or pixel not recognised.\n')
    sys.exit(1)



