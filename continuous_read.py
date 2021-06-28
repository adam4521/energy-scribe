#! /usr/bin/env python3

import blinkt
import sys
import os
import time
import subprocess


LOGDIR = '/media/usb/kwhmeter'
LOGFILE = LOGDIR + '/' + time.strftime('%Y%m%d-%H.%M.%S', time.gmtime()) + '.csv'
TIME_SLICE = 10.0

# Select meter hardware
# Uncomment READMETER and CSVHEADERS to switch to different meter hardware
#READMETER = './current_cost.py'
#CSVHEADERS = '"Time", "Watts #1", "Watts #2", "Watts #3", "Watts #4", "Watts #5", "Watts #6", "Watts #7", "Watts #8", "Watts #9"'
#READMETER = './hiking_dds238_2.py'
#CSVHEADERS = '"Time","Voltage","Current","Power","Reactive power","Power factor","Frequency","Cumulative energy"'
READMETER = './schneider_iEM2150_with_semaphore.py'
CSVHEADERS = '"Time","Voltage","Current","Power","Reactive power","Power factor","Power factor direction","Frequency","Cumulative energy"'


COLOURS = { 'red': (200,0,0), 'green': (0,200,0), 'blue': (0,0,200), 'yellow': (200,200,0),\
        'cyan': (0,200,200), 'magenta': (200,0,200), 'white': (200,200,200), 'off': (0,0,0) }

def set_pixel(index, colour):
    try:
        col = COLOURS[colour]
        blinkt.set_pixel(index, col[0], col[1], col[2])
        blinkt.show()
    except:
        sys.stderr.write("Index or colour was out of range.\n")
        raise ValueError()

def open_log_file():
    try:
        f = open(LOGFILE, 'w+')
        return f
    except:
        sys.stderr.write("Couldn't open the log file.\n")
        raise OSError()

def get_readings():
    try:
        result = subprocess.run([READMETER], stdout = subprocess.PIPE)
        if result.returncode == 0:
            return result.stdout.decode('utf-8')
        else:
            sys.stderr.write("Check serial connection.\n")
            raise ConnectionError()
    except subprocess.CalledProcessError:
        sys.stderr.write("Problem running acquisition sub-process.\n")
        raise ConnectionError()



# We start here
try:
    blinkt.set_clear_on_exit(False)
    blinkt.set_brightness(0.1)

    set_pixel(0, 'magenta')
    captures = 0
    log_file = open_log_file()
    log_file.write(CSVHEADERS + '\n')
    time_start = time.time()
    def sleeping():
        # accurately loops by time slice by syncing to system clock
        time.sleep(TIME_SLICE - ((time.time() - time_start) % TIME_SLICE))
    while True:
        try:
            set_pixel(1, 'blue')
            readings = get_readings()
        except ConnectionError:
            set_pixel(1, 'red')
            sleeping()
            continue
        set_pixel(2, 'green')
        log_file.write(readings)
        set_pixel(1, 'off')
        set_pixel(2, 'off')
        captures = captures + 1
        if captures % 10 == 0:
            # clears cached writes to USB stick every 10 cycles
            log_file.flush()
            os.fsync(log_file.fileno())
        sleeping() 

except ConnectionError:
    sys.stderr.write('Error connecting to sub-process or meter hardware.\n')
    set_pixel(0, 'red')
    set_pixel(1, 'red')
    set_pixel(2, 'off')
    log_file.close()
    sys.exit(1)

except OSError:
    sys.stderr.write('Error writing the log file.\n')
    set_pixel(0, 'red')
    set_pixel(1, 'off')
    set_pixel(2, 'red')
    log_file.close()
    sys.exit(1)

except:
    sys.stderr.write('Unhandled error.\n')
    set_pixel(0, 'red')
    set_pixel(1, 'off')
    set_pixel(2, 'off')
    log_file.close()
    sys.exit(1)





