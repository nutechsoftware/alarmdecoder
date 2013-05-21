"""
Contains different types of devices belonging to the AD2USB family.
"""

import usb.core
import usb.util
import time
import threading
import serial
import serial.tools.list_ports
import traceback
from pyftdi.pyftdi.ftdi import *
from pyftdi.pyftdi.usbtools import *
from . import util
from .event import event

class Device(object):
    """
    Generic parent device to all AD2USB products.
    """

    # Generic device events
    on_open = event.Event('Called when the device has been opened')
    on_close = event.Event('Called when the device has been closed')
    on_read = event.Event('Called when a line has been read from the device')
    on_write = event.Event('Called when data has been written to the device')

    def __init__(self):
        pass

    def __del__(self):
        pass

    class ReadThread(threading.Thread):
        """
        Reader thread which processes messages from the device.
        """

        def __init__(self, device):
            """
            Constructor
            """
            threading.Thread.__init__(self)
            self._device = device
            self._running = False

        def stop(self):
            """
            Stops the running thread.
            """
            self._running = False

        def run(self):
            """
            The actual read process.
            """
            self._running = True

            while self._running:
                try:
                    self._device.read_line(timeout=10)
                except util.CommError, err:
                    traceback.print_exc(err)    # TEMP
                except util.TimeoutError, err:
                    pass

                time.sleep(0.01)

class USBDevice(Device):
    """
    AD2USB device exposed with PyFTDI's interface.
    """

    # Constants
    FTDI_VENDOR_ID = 0x0403
    FTDI_PRODUCT_ID = 0x6001
    BAUDRATE = 115200

    @staticmethod
    def find_all():
        """
        Returns all FTDI devices matching our vendor and product IDs.
        """

        devices = []

        try:
            devices = Ftdi.find_all([(USBDevice.FTDI_VENDOR_ID, USBDevice.FTDI_PRODUCT_ID)], nocache=True)
        except (usb.core.USBError, FtdiError), err:
            raise util.CommError('Error enumerating AD2USB devices: {0}'.format(str(err)))

        return devices

    def __init__(self, vid=FTDI_VENDOR_ID, pid=FTDI_PRODUCT_ID, serial=None, description=None, interface=0):
        """
        Constructor
        """

        Device.__init__(self)

        self._vendor_id = vid
        self._product_id = pid
        self._serial_number = serial
        self._description = description
        self._buffer = ''
        self._device = Ftdi()
        self._running = False
        self._interface = interface

        self._read_thread = Device.ReadThread(self)

    def open(self, baudrate=BAUDRATE, interface=None, index=0):
        """
        Opens the device.
        """
        self._running = True

        # Set up defaults
        if baudrate is None:
            baudrate = USBDevice.BAUDRATE

        if self._interface is None and interface is None:
            self._interface = 0

        if interface is not None:
            self._interface = interface

        if index is None:
            index = 0

        # Open the device and start up the thread.
        try:
            self._device.open(self._vendor_id,
                             self._product_id,
                             self._interface,
                             index,
                             self._serial_number,
                             self._description)

            self._device.set_baudrate(baudrate)
        except (usb.core.USBError, FtdiError), err:
            self.on_close()

            raise util.CommError('Error opening AD2USB device: {0}'.format(str(err)))
        else:
            self._read_thread.start()

            self.on_open((self._serial_number, self._description))

    def close(self):
        """
        Closes the device.
        """
        try:
            self._running = False
            self._read_thread.stop()

            self._device.close()

            # HACK: Probably should fork pyftdi and make this call in .close().
            self._device.usb_dev.attach_kernel_driver(self._interface)
        except (FtdiError, usb.core.USBError):
            pass

        self.on_close()

    def close_reader(self):
        """
        Stops the reader thread.
        """
        self._read_thread.stop()

    def write(self, data):
        """
        Writes data to the device.
        """
        self._device.write_data(data)

        self.on_write(data)

    def read(self):
        """
        Reads a single character from the device.
        """
        return self._device.read_data(1)

    def read_line(self, timeout=0.0):
        """
        Reads a line from the device.
        """
        start_time = time.time()
        got_line = False
        ret = None

        try:
            while self._running:
                buf = self._device.read_data(1)

                if buf != '':
                    self._buffer += buf

                    if buf == "\n":
                        if len(self._buffer) > 1:
                            if self._buffer[-2] == "\r":
                                self._buffer = self._buffer[:-2]

                                # ignore if we just got \r\n with nothing else in the buffer.
                                if len(self._buffer) != 0:
                                    got_line = True
                                    break
                        else:
                            self._buffer = self._buffer[:-1]

                if timeout > 0 and time.time() - start_time > timeout:
                    raise util.TimeoutError('Timeout while waiting for line terminator.')

        except (usb.core.USBError, FtdiError), err:
            raise util.CommError('Error reading from AD2USB device: {0}'.format(str(err)))
        else:
            if got_line:
                ret = self._buffer
                self._buffer = ''

                self.on_read(ret)

        return ret


class SerialDevice(Device):
    """
    AD2USB or AD2SERIAL device exposed with the pyserial interface.
    """

    # Constants
    BAUDRATE = 19200

    @staticmethod
    def find_all():
        """
        Returns all serial ports present.
        """
        devices = []

        try:
            devices = serial.tools.list_ports.comports()
        except Exception, err:
            raise util.CommError('Error enumerating AD2SERIAL devices: {0}'.format(str(err)))

        return devices

    def __init__(self, interface=None):
        """
        Constructor
        """
        Device.__init__(self)

        self._device = serial.Serial(timeout=0)     # Timeout = non-blocking to match pyftdi.
        self._read_thread = Device.ReadThread(self)
        self._buffer = ''
        self._running = False
        self._interface = interface

    def __del__(self):
        """
        Destructor
        """
        pass

    def open(self, baudrate=BAUDRATE, interface=None, index=None):
        """
        Opens the device.
        """

        # Set up the defaults
        if baudrate is None:
            baudrate = SerialDevice.BAUDRATE

        if self._interface is None and interface is None:
            raise util.NoDeviceError('No AD2SERIAL device interface specified.')

        if interface is not None:
            self._interface = interface

        self._device.baudrate = baudrate
        self._device.port = self._interface

        # Open the device and start up the reader thread.
        try:
            self._device.open()

            self._running = True
        except (serial.SerialException, ValueError), err:
            self.on_close()

            raise util.NoDeviceError('Error opening AD2SERIAL device on port {0}.'.format(interface))
        else:
            self.on_open((None, "AD2SERIAL"))   # TODO: Fixme.

            self._read_thread.start()

    def close(self):
        """
        Closes the device.
        """
        try:
            self._running = False
            self._read_thread.stop()

            self._device.close()
        except Exception, err:
            pass

        self.on_close()

    def close_reader(self):
        """
        Stops the reader thread.
        """
        self._read_thread.stop()

    def write(self, data):
        """
        Writes data to the device.
        """
        try:
            self._device.write(data)
        except serial.SerialTimeoutException, err:
            pass
        else:
            self.on_write(data)

    def read(self):
        """
        Reads a single character from the device.
        """
        return self._device.read(1)

    def read_line(self, timeout=0.0):
        """
        Reads a line from the device.
        """
        start_time = time.time()
        got_line = False
        ret = None

        try:
            while self._running:
                buf = self._device.read(1)

                if buf != '' and buf != "\xff":     # AD2SERIAL specifically apparently sends down \xFF on boot.
                    self._buffer += buf

                    if buf == "\n":
                        if len(self._buffer) > 1:
                            if self._buffer[-2] == "\r":
                                self._buffer = self._buffer[:-2]

                                # ignore if we just got \r\n with nothing else in the buffer.
                                if len(self._buffer) != 0:
                                    got_line = True
                                    break
                        else:
                            self._buffer = self._buffer[:-1]

                if timeout > 0 and time.time() - start_time > timeout:
                    raise util.TimeoutError('Timeout while waiting for line terminator.')

        except (OSError, serial.SerialException), err:
            raise util.CommError('Error reading from AD2SERIAL device: {0}'.format(str(err)))
        else:
            if got_line:
                ret = self._buffer
                self._buffer = ''

                self.on_read(ret)

        return ret
