"""
This module contains the :py:class:`SerialDevice` interface for the `AD2USB`_, `AD2SERIAL`_ or `AD2PI`_.

.. _AD2USB: http://www.alarmdecoder.com
.. _AD2SERIAL: http://www.alarmdecoder.com
.. _AD2PI: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import threading
import serial
import serial.tools.list_ports
import select
import sys
from .base_device import Device
from ..util import CommError, TimeoutError, NoDeviceError, bytes_hack, filter_ad2prot_byte


class SerialDevice(Device):
    """
    `AD2USB`_, `AD2SERIAL`_ or `AD2PI`_ device utilizing the PySerial interface.
    """

    # Constants
    BAUDRATE = 19200
    """Default baudrate for Serial devices."""

    @staticmethod
    def find_all(pattern=None):
        """
        Returns all serial ports present.

        :param pattern: pattern to search for when retrieving serial ports
        :type pattern: string

        :returns: list of devices
        :raises: :py:class:`~alarmdecoder.util.CommError`
        """
        devices = []

        try:
            if pattern:
                devices = serial.tools.list_ports.grep(pattern)
            else:
                devices = serial.tools.list_ports.comports()

        except serial.SerialException as err:
            raise CommError('Error enumerating serial devices: {0}'.format(str(err)), err)

        return devices

    @property
    def interface(self):
        """
        Retrieves the interface used to connect to the device.

        :returns: interface used to connect to the device
        """
        return self._port

    @interface.setter
    def interface(self, value):
        """
        Sets the interface used to connect to the device.

        :param value: name of the serial device
        :type value: string
        """
        self._port = value

    def __init__(self, interface=None):
        """
        Constructor

        :param interface: device to open
        :type interface: string
        """
        Device.__init__(self)

        self._port = interface
        self._id = interface
        # Timeout = non-blocking to match pyftdi.
        self._device = serial.Serial(timeout=0, writeTimeout=0)

    def open(self, baudrate=BAUDRATE, no_reader_thread=False):
        """
        Opens the device.

        :param baudrate: baudrate to use with the device
        :type baudrate: int
        :param no_reader_thread: whether or not to automatically start the
                                 reader thread.
        :type no_reader_thread: bool

        :raises: :py:class:`~alarmdecoder.util.NoDeviceError`
        """
        # Set up the defaults
        if baudrate is None:
            baudrate = SerialDevice.BAUDRATE

        if self._port is None:
            raise NoDeviceError('No device interface specified.')

        self._read_thread = Device.ReadThread(self)

        # Open the device and start up the reader thread.
        try:
            self._device.port = self._port
            self._device.open()
            # NOTE: Setting the baudrate before opening the
            #       port caused issues with Moschip 7840/7820
            #       USB Serial Driver converter. (mos7840)
            #
            #       Moving it to this point seems to resolve
            #       all issues with it.
            self._device.baudrate = baudrate

        except (serial.SerialException, ValueError, OSError) as err:
            raise NoDeviceError('Error opening device on {0}.'.format(self._port), err)

        else:
            self._running = True
            self.on_open()

            if not no_reader_thread:
                self._read_thread.start()

        return self

    def close(self):
        """
        Closes the device.
        """
        try:
            Device.close(self)

        except Exception:
            pass

    def fileno(self):
        """
        Returns the file number associated with the device

        :returns: int
        """
        return self._device.fileno()

    def write(self, data):
        """
        Writes data to the device.

        :param data: data to write
        :type data: string

        :raises: py:class:`~alarmdecoder.util.CommError`
        """
        try:
            # Hack to support unicode under Python 2.x
            if isinstance(data, str) or (sys.version_info < (3,) and isinstance(data, unicode)):
                data = data.encode('utf-8')

            self._device.write(data)

        except serial.SerialTimeoutException:
            pass

        except serial.SerialException as err:
            raise CommError('Error writing to device.', err)

        else:
            self.on_write(data=data)

    def read(self):
        """
        Reads a single character from the device.

        :returns: character read from the device
        :raises: :py:class:`~alarmdecoder.util.CommError`
        """
        data = b''

        try:
            read_ready, _, _ = select.select([self._device.fileno()], [], [], 0.5)

            if len(read_ready) != 0:
                data = filter_ad2prot_byte(self._device.read(1))

        except serial.SerialException as err:
            raise CommError('Error reading from device: {0}'.format(str(err)), err)

        return data.decode('utf-8')

    def read_line(self, timeout=0.0, purge_buffer=False):
        """
        Reads a line from the device.

        :param timeout: read timeout
        :type timeout: float
        :param purge_buffer: Indicates whether to purge the buffer prior to
                             reading.
        :type purge_buffer: bool

        :returns: line that was read
        :raises: :py:class:`~alarmdecoder.util.CommError`, :py:class:`~alarmdecoder.util.TimeoutError`
        """

        def timeout_event():
            """Handles read timeout event"""
            timeout_event.reading = False
        timeout_event.reading = True

        if purge_buffer:
            self._buffer = b''

        got_line, ret = False, None

        timer = threading.Timer(timeout, timeout_event)
        if timeout > 0:
            timer.start()

        try:
            while timeout_event.reading:
                read_ready, _, _ = select.select([self._device.fileno()], [], [], 0.5)

                if len(read_ready) == 0:
                    continue

                buf = filter_ad2prot_byte(self._device.read(1))

                if buf != b'':
                    self._buffer += buf

                    if buf == b"\n":
                        self._buffer = self._buffer.rstrip(b"\r\n")

                        if len(self._buffer) > 0:
                            got_line = True
                            break
        except (OSError, serial.SerialException) as err:
            raise CommError('Error reading from device: {0}'.format(str(err)), err)

        else:
            if got_line:
                ret, self._buffer = self._buffer, b''

                self.on_read(data=ret)

            else:
                raise TimeoutError('Timeout while waiting for line terminator.')

        finally:
            timer.cancel()

        return ret.decode('utf-8')

    def purge(self):
        """
        Purges read/write buffers.
        """
        self._device.flushInput()
        self._device.flushOutput()
