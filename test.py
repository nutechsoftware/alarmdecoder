#!/usr/bin/env python

import pyad2usb.ad2usb
import time
import signal
import traceback

running = True

def signal_handler(signal, frame):
    global running

    running = False

def handle_open(sender, args):
    print 'opened', args

def handle_close(sender, args):
    print 'closed', args

def handle_read(sender, args):
    print 'read', args

def handle_write(sender, args):
    print 'write', args

def handle_attached(sender, args):
    print 'attached', args

def handle_detached(sender, args):
    print 'detached', args


signal.signal(signal.SIGINT, signal_handler)

try:
    #overseer = pyad2usb.ad2usb.Overseer(attached_event=handle_attached, detached_event=handle_detached)
    #overseer.start()

    #dev = pyad2usb.ad2usb.AD2USB()
    #dev = overseer.get_device()

    #dev = pyad2usb.ad2usb.Overseer.create()
    dev = pyad2usb.ad2usb.devices.SerialDevice()
    #dev = pyad2usb.ad2usb.devices.USBDevice()#serial='A101A429', description='FT232R USB UART')
    dev.on_open += handle_open
    dev.on_close += handle_close
    dev.on_read += handle_read
    dev.on_write += handle_write
    #dev.open(baudrate=115200, interface='/dev/ttyUSB5')
    dev.open(baudrate=19200, interface='/dev/ttyUSB0')
    #dev.open()

    while running:
        time.sleep(0.1)

    dev.close()
    #overseer.close()

    #wut.close()
except Exception, err:
    #print 'Error: {0}'.format(str(err))
    traceback.print_exc(err)
