#! /usr/bin/env python3
# For raspberry pi with blinkt led accessory
# Usage: 
# blinkt.py 2 'red'                  to light 3rd pixel (numbered 0 to 7)
# blinkt.py 2 'off'                  to extinguish 3rd pixel


import blinkt
import sys


colours = { 'red': (200,0,0), 'green': (0,200,0), 'blue': (0,0,200), 'yellow': (200,200,0),\
        'cyan': (0,200,200), 'magenta': (200,0,200), 'white': (200,200,200), 'off': (0,0,0) }


if __name__ == '__main__':
    try:
        colour = colours[sys.argv[2]]
        blinkt.set_pixel(sys.argv[1], colour[0], colour[1], colour[2])
    except:
        sys.stderr.write('Colour or pixel not recognised.\n')
        sys.exit(1)



