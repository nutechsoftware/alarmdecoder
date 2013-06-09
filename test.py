#!/usr/bin/env python

import pyad2usb.ad2usb
import time
import signal
import traceback
import sys
import logging

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

def handle_power_changed(sender, args):
    print 'power changed', args

def handle_alarm_bell(sender, args):
    print 'alarm', args

def handle_bypass(sender, args):
    print 'bypass', args

def handle_message(sender, args):
    print args

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
        if handle_firmware.wait_tick > 0: print ""
        print "Rebooting device.."
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

def handle_boot(sender, args):
    print 'boot', args

def handle_config(sender, args):
    print 'config', args

def upload_usb():
    dev = pyad2usb.ad2usb.devices.USBDevice()

    dev.open(no_reader_thread=True)
    pyad2usb.ad2usb.util.Firmware.upload(dev, 'tmp/ademcoemu_V2_2a_6.hex', handle_firmware)
    dev.close()

def upload_serial():
    dev = pyad2usb.ad2usb.devices.SerialDevice(interface='/dev/ttyUSB2')

    dev.open()
    pyad2usb.ad2usb.util.Firmware.upload(dev, 'tmp/ademcoemu_V2_2a_6.hex', handle_firmware)
    dev.close()

def upload_usb_serial():
    dev = pyad2usb.ad2usb.devices.SerialDevice(interface='/dev/ttyUSB5')

    dev.open(baudrate=115200)
    pyad2usb.ad2usb.util.Firmware.upload(dev, 'tmp/ademcoemu_V2_2a_6.hex', handle_firmware)
    dev.close()

def upload_socket():
    dev = pyad2usb.ad2usb.devices.SocketDevice(interface=('localhost', 10000))

    dev.open()
    pyad2usb.ad2usb.util.Firmware.upload(dev, 'tmp/ademcoemu_V2_2a_6.hex', handle_firmware)
    dev.close()

def test_usb():
    dev = pyad2usb.ad2usb.devices.USBDevice()

    a2u = pyad2usb.ad2usb.AD2USB(dev)
    a2u.on_open += handle_open
    a2u.on_close += handle_close
    a2u.on_read += handle_read
    a2u.on_write += handle_write

    a2u.on_power_changed += handle_power_changed
    a2u.on_alarm += handle_alarm_bell
    a2u.on_bypass += handle_bypass

    a2u.open()

    print dev._id

    while running:
        time.sleep(0.1)

    a2u.close()

def test_serial():
    dev = pyad2usb.ad2usb.devices.SerialDevice(interface='/dev/ttyUSB0')

    a2u = pyad2usb.ad2usb.AD2USB(dev)
    a2u.on_open += handle_open
    a2u.on_close += handle_close
    #a2u.on_read += handle_read
    #a2u.on_write += handle_write

    a2u.on_message += handle_message
    a2u.on_power_changed += handle_power_changed
    a2u.on_alarm += handle_alarm_bell
    a2u.on_bypass += handle_bypass

    a2u.open(no_reader_thread=False)
    print a2u._device._device
    #print a2u._device.read_line()
    #dev.open()

    print dev._id

    while running:
        time.sleep(0.1)

    a2u.close()
    #dev.close()

def test_usb_serial():
    dev = pyad2usb.ad2usb.devices.SerialDevice(interface='/dev/ttyUSB5')

    a2u = pyad2usb.ad2usb.AD2USB(dev)
    a2u.on_open += handle_open
    a2u.on_close += handle_close
    a2u.on_read += handle_read
    a2u.on_write += handle_write

    a2u.open(baudrate=115200)
    print dev._id

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

def test_socket():
    dev = pyad2usb.ad2usb.devices.SocketDevice(interface=("singularity.corp.nutech.com", 10000))

    a2u = pyad2usb.ad2usb.AD2USB(dev)
    a2u.on_open += handle_open
    a2u.on_close += handle_close
    #a2u.on_read += handle_read
    #a2u.on_write += handle_write

    a2u.on_message += handle_message
    a2u.on_power_changed += handle_power_changed
    a2u.on_alarm += handle_alarm_bell
    a2u.on_bypass += handle_bypass
    a2u.on_boot += handle_boot
    a2u.on_config_received += handle_config

    a2u.open()
    #a2u.save_config()
    #a2u.reboot()
    a2u.get_config()

    while running:
        time.sleep(0.1)

    a2u.close()

def test_no_read_thread():
    #a2u = pyad2usb.ad2usb.Overseer.create()


    #a2u.on_open += handle_open
    #a2u.on_close += handle_close
    #a2u.on_read += handle_read
    #a2u.on_write += handle_write

    #a2u.open(no_reader_thread=True)

    dev = pyad2usb.ad2usb.devices.SerialDevice(interface='/dev/ttyUSB0')
    dev.open(no_reader_thread=True)

    #print 'alive?', a2u._device._read_thread.is_alive()
    while 1:
        line = dev.read_line(timeout=5)
        print line
        line = dev.read_line(timeout=5)
        print line
        #time.sleep(0.1)

    dev.close()

def test_serial_grep():
    re =  pyad2usb.devices.SerialDevice.find_all(pattern='VID:PID=9710:7840')
    for x in re:
        print x

def test_double_panel_write():
    dev = pyad2usb.ad2usb.devices.SerialDevice(interface='/dev/ttyUSB4')
    dev2 = pyad2usb.ad2usb.devices.SerialDevice(interface='/dev/ttyUSB5')

    dev.open(no_reader_thread=True)
    print dev._device

    dev2.open(no_reader_thread=True)
    print dev2._device
    #print a2u._device.read_line()
    #dev.open()

    print 'Writing characters..'
    dev.write('*****')
    dev2.write('*****')

    print 'Reading..'

    dev_res = dev.read_line()
    print dev.id, dev_res

    dev2_res = dev2.read_line()
    print dev2.id, dev2_res

    dev.close()
    dev2.close()

try:
    logging.basicConfig(level=logging.DEBUG)
    signal.signal(signal.SIGINT, signal_handler)

    #test_serial()
    #upload_serial()

    #test_usb()
    #test_usb_serial()
    #test_factory()
    #test_factory_watcher()
    #upload_usb()
    #upload_usb_serial()

    test_socket()
    #upload_socket()

    #test_no_read_thread()
    #test_serial_grep()

    #test_double_panel_write()

except Exception, err:
    traceback.print_exc(err)
