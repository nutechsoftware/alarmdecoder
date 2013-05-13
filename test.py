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
    overseer = pyad2usb.ad2usb.Overseer(attached_event=handle_attached, detached_event=handle_detached)
    #overseer.start()

    """wut = pyad2usb.ad2usb.AD2USB()

    wut.on_open += handle_open
    wut.on_close += handle_close
    wut.on_read += handle_read
    wut.on_write += handle_write

    wut.open()"""

    while running:
        time.sleep(0.1)

    overseer.stop()

    #wut.close()
except Exception, err:
    print 'Error: {0}'.format(str(err))
    #traceback.print_exc(err)
