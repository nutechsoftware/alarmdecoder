"""
Contains different types of devices belonging to the AD2USB family.
"""

import usb.core
import usb.util
import time
import threading
import serial
import serial.tools.list_ports
import socket
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
        self._id = ''

        self._read_thread = Device.ReadThread(self)

    def open(self, baudrate=BAUDRATE, interface=None, index=0, no_reader_thread=False):
        """
        Opens the device.
        """
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

            self._id = 'USB {0}:{1}'.format(self._device.usb_dev.bus, self._device.usb_dev.address)
        except (usb.core.USBError, FtdiError), err:
            self.on_close()

            raise util.NoDeviceError('Error opening AD2USB device: {0}'.format(str(err)))
        else:
            self._running = True
            if not no_reader_thread:
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

    @property
    def id(self):
        return self._id

    def is_reader_alive(self):
        """
        Indicates whether or not the reader thread is alive.
        """
        return self._read_thread.is_alive()

    def stop_reader(self):
        """
        Stops the reader thread.
        """
        self._read_thread.stop()

    def write(self, data):
        """
        Writes data to the device.
        """
        try:
            self._device.write_data(data)

            self.on_write(data)
        except FtdiError, err:
            raise util.CommError('Error writing to AD2USB device.')

    def read(self):
        """
        Reads a single character from the device.
        """
        return self._device.read_data(1)

    def read_line(self, timeout=0.0):
        """
        Reads a line from the device.
        """
        def timeout_event():
            timeout_event.reading = False

        timeout_event.reading = True

        got_line = False
        ret = None

        timer = None
        if timeout > 0:
            timer = threading.Timer(timeout, timeout_event)
            timer.start()

        try:
            while timeout_event.reading:
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

                time.sleep(0.001)

        except (usb.core.USBError, FtdiError), err:
            raise util.CommError('Error reading from AD2USB device: {0}'.format(str(err)))
        else:
            if got_line:
                ret = self._buffer
                self._buffer = ''

                self.on_read(ret)

        if timer:
            if timer.is_alive():
                timer.cancel()
            else:
                raise util.TimeoutError('Timeout while waiting for line terminator.')

        return ret


class SerialDevice(Device):
    """
    AD2USB or AD2SERIAL device exposed with the pyserial interface.
    """

    # Constants
    BAUDRATE = 19200

    @staticmethod
    def find_all(pattern=None):
        """
        Returns all serial ports present.
        """
        devices = []

        try:
            if pattern:
                devices = serial.tools.list_ports.grep(pattern)
            else:
                devices = serial.tools.list_ports.comports()
        except Exception, err:
            raise util.CommError('Error enumerating AD2SERIAL devices: {0}'.format(str(err)))

        return devices

    def __init__(self, interface=None):
        """
        Constructor
        """
        Device.__init__(self)

        self._device = serial.Serial(timeout=0, writeTimeout=0)     # Timeout = non-blocking to match pyftdi.
        self._read_thread = Device.ReadThread(self)
        self._buffer = ''
        self._running = False
        self._interface = interface
        self._id = interface

    def __del__(self):
        """
        Destructor
        """
        pass

    def open(self, baudrate=BAUDRATE, interface=None, index=None, no_reader_thread=False):
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

        self._device.port = self._interface

        # Open the device and start up the reader thread.
        try:
            self._device.open()
            self._device.baudrate = baudrate            # NOTE: Setting the baudrate before opening the
                                                        #       port caused issues with Moschip 7840/7820
                                                        #       USB Serial Driver converter. (mos7840)
                                                        #
                                                        #       Moving it to this point seems to resolve
                                                        #       all issues with it.
            self._id = '{0}'.format(self._interface)

        except (serial.SerialException, ValueError), err:
            self.on_close()

            raise util.NoDeviceError('Error opening AD2SERIAL device on port {0}.'.format(interface))
        else:
            self._running = True
            self.on_open((None, "AD2SERIAL"))   # TODO: Fixme.

            if not no_reader_thread:
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

    @property
    def id(self):
        return self._id

    def is_reader_alive(self):
        """
        Indicates whether or not the reader thread is alive.
        """
        return self._read_thread.is_alive()

    def stop_reader(self):
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
        except serial.SerialException, err:
            raise util.CommError('Error writing to serial device.')
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

        def timeout_event():
            timeout_event.reading = False

        timeout_event.reading = True

        got_line = False
        ret = None

        timer = None
        if timeout > 0:
            timer = threading.Timer(timeout, timeout_event)
            timer.start()

        try:
            while timeout_event.reading:
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

                time.sleep(0.001)

        except (OSError, serial.SerialException), err:
            timer.cancel()

            raise util.CommError('Error reading from AD2SERIAL device: {0}'.format(str(err)))
        else:
            if got_line:
                ret = self._buffer
                self._buffer = ''

                self.on_read(ret)

        if timer:
            if timer.is_alive():
                timer.cancel()
            else:
                raise util.TimeoutError('Timeout while waiting for line terminator.')

        return ret

class SocketDevice(Device):
    """
    Device that supports communication with an AD2USB that is exposed via ser2sock or another
    Serial to IP interface.
    """

    def __init__(self, interface=None):
        """
        Constructor
        """
        self._host = "localhost"
        self._port = 10000
        self._device = None
        self._buffer = ''
        self._running = False
        self._id = ''

        self._read_thread = Device.ReadThread(self)

    def __del__(self):
        """
        Destructor
        """
        pass

    def open(self, baudrate=None, interface=None, index=0, no_reader_thread=False):
        """
        Opens the device.
        """
        if interface is not None:
            self._host, self._port = interface

        try:
            self._device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._device.connect((self._host, self._port))
            self._id = '{0}:{1}'.format(self._host, self._port)

        except socket.error, err:
            self.on_close()

            raise util.NoDeviceError('Error opening AD2SOCKET device at {0}:{1}'.format(self._host, self._port))
        else:
            self._running = True

            self.on_open((None, "AD2SOCKET"))   # TEMP: Change me.

            if not no_reader_thread:
                self._read_thread.start()

    def close(self):
        """
        Closes the device.
        """
        self._running = False

        try:
            self._read_thread.stop()
            self._device.shutdown(socket.SHUT_RDWR)     # Make sure that it closes immediately.
            self._device.close()
        except:
            pass

        self.on_close()

    @property
    def id(self):
        return self._id

    def is_reader_alive(self):
        """
        Indicates whether or not the reader thread is alive.
        """
        return self._read_thread.is_alive()

    def stop_reader(self):
        """
        Stops the reader thread.
        """
        self._read_thread.stop()

    def write(self, data):
        """
        Writes data to the device.
        """
        data_sent = self._device.send(data)

        if data_sent == 0:
            raise util.CommError('Error while sending data.')
        else:
            self.on_write(data)

        return data_sent

    def read(self):
        """
        Reads a single character from the device.
        """
        try:
            data = self._device.recv(1)
        except socket.error, err:
            raise util.CommError('Error while reading from device: {0}'.format(str(err)))

        # ??? - Should we trigger an on_read here as well?

        return data

    def read_line(self, timeout=0.0):
        """
        Reads a line from the device.
        """
        def timeout_event():
            timeout_event.reading = False

        timeout_event.reading = True

        got_line = False
        ret = None

        timer = None
        if timeout > 0:
            timer = threading.Timer(timeout, timeout_event)
            timer.start()

        try:
            while timeout_event.reading:
                buf = self._device.recv(1)

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

                time.sleep(0.001)

        except socket.error, err:
            raise util.CommError('Error reading from Socket device: {0}'.format(str(err)))
        else:
            if got_line:
                ret = self._buffer
                self._buffer = ''

                self.on_read(ret)

        if timer:
            if timer.is_alive():
                timer.cancel()
            else:
                raise util.TimeoutError('Timeout while waiting for line terminator.')

        return ret
