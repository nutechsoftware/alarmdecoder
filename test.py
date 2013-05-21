#!/usr/bin/env python

import pyad2usb.ad2usb
import time
import signal
import traceback
import sys

running = True

def signal_handler(signal, frame):
    global running

    running = False

def handle_open(sender, args):
    print 'O', args

def handle_close(sender, args):
    print 'C', args

def handle_read(sender, args):
    print '<', args

def handle_write(sender, args):
    print '>', args

def handle_attached(sender, args):
    print '+', args

def handle_detached(sender, args):
    print '-', args

def handle_firmware(stage):
    if stage == pyad2usb.ad2usb.util.Firmware.STAGE_START:
        handle_firmware.wait_tick = 0
        handle_firmware.upload_tick = 0
    elif stage == pyad2usb.ad2usb.util.Firmware.STAGE_WAITING:
        if handle_firmware.wait_tick == 0:
            sys.stdout.write('Waiting for device.')
        handle_firmware.wait_tick += 1

        sys.stdout.write('.')
        sys.stdout.flush()
    elif stage == pyad2usb.ad2usb.util.Firmware.STAGE_BOOT:
        print "\r\nRebooting device.."
    elif stage == pyad2usb.ad2usb.util.Firmware.STAGE_LOAD:
        print 'Waiting for boot loader..'
    elif stage == pyad2usb.ad2usb.util.Firmware.STAGE_UPLOADING:
        if handle_firmware.upload_tick == 0:
            sys.stdout.write('Uploading firmware.')

        handle_firmware.upload_tick += 1

        if handle_firmware.upload_tick % 30 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
    elif stage == pyad2usb.ad2usb.util.Firmware.STAGE_DONE:
        print "\r\nDone!"

def upload_usb():
    dev = pyad2usb.ad2usb.devices.USBDevice()

    dev.open()
    pyad2usb.ad2usb.util.Firmware.upload(dev, 'tmp/ademcoemu_V2_2a_6.hex', handle_firmware)
    dev.close()

def upload_serial():
    dev = pyad2usb.ad2usb.devices.SerialDevice(interface='/dev/ttyUSB0')

    dev.open()
    pyad2usb.ad2usb.util.Firmware.upload(dev, 'tmp/ademcoemu_V2_2a_6.hex', handle_firmware)
    dev.close()

def upload_usb_serial():
    dev = pyad2usb.ad2usb.devices.SerialDevice(interface='/dev/ttyUSB5')

    dev.open(baudrate=115200)
    pyad2usb.ad2usb.util.Firmware.upload(dev, 'tmp/ademcoemu_V2_2a_6.hex', handle_firmware)
    dev.close()

def test_usb():
    dev = pyad2usb.ad2usb.devices.USBDevice()

    a2u = pyad2usb.ad2usb.AD2USB(dev)
    a2u.on_open += handle_open
    a2u.on_close += handle_close
    a2u.on_read += handle_read
    a2u.on_write += handle_write

    a2u.open()

    while running:
        time.sleep(0.1)

    a2u.close()

def test_serial():
    dev = pyad2usb.ad2usb.devices.SerialDevice(interface='/dev/ttyUSB0')

    a2u = pyad2usb.ad2usb.AD2USB(dev)
    a2u.on_open += handle_open
    a2u.on_close += handle_close
    a2u.on_read += handle_read
    a2u.on_write += handle_write

    a2u.open()

    while running:
        time.sleep(0.1)

    a2u.close()

def test_usb_serial():
    dev = pyad2usb.ad2usb.devices.SerialDevice(interface='/dev/ttyUSB5')

    a2u = pyad2usb.ad2usb.AD2USB(dev)
    a2u.on_open += handle_open
    a2u.on_close += handle_close
    a2u.on_read += handle_read
    a2u.on_write += handle_write

    a2u.open(baudrate=115200)

    while running:
        time.sleep(0.1)

    a2u.close()

def test_factory():
    a2u = pyad2usb.ad2usb.Overseer.create()

    a2u.on_open += handle_open
    a2u.on_close += handle_close
    a2u.on_read += handle_read
    a2u.on_write += handle_write

    a2u.open()

    while running:
        time.sleep(0.1)

    a2u.close()

def test_factory_watcher():
    overseer = pyad2usb.ad2usb.Overseer(attached_event=handle_attached, detached_event=handle_detached)

    a2u = overseer.get_device()

    a2u.on_open += handle_open
    a2u.on_close += handle_close
    a2u.on_read += handle_read
    a2u.on_write += handle_write

    a2u.open()

    while running:
        time.sleep(0.1)

    a2u.close()
    overseer.close()

try:
    signal.signal(signal.SIGINT, signal_handler)

    #test_serial()
    #upload_serial()

    #test_usb()
    #test_usb_serial()
    #test_factory()
    #test_factory_watcher()
    upload_usb()
    #upload_usb_serial()

except Exception, err:
    traceback.print_exc(err)
