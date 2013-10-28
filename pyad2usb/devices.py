"""
Contains different types of devices belonging to the AD2USB family.

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import usb.core, usb.util
import time
import threading
import serial, serial.tools.list_ports
import socket
from OpenSSL import SSL, crypto
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
        """
        Constructor
        """
        self._id = ''
        self._buffer = ''
        self._device = None
        self._running = False
        self._read_thread = Device.ReadThread(self)

    @property
    def id(self):
        """
        Retrieve the device ID.

        :returns: The identification string for the device.
        """
        return self._id

    @id.setter
    def id(self, value):
        """
        Sets the device ID.

        :param value: The device identification.
        :type value: str
        """
        self._id = value

    def is_reader_alive(self):
        """
        Indicates whether or not the reader thread is alive.

        :returns: Whether or not the reader thread is alive.
        """
        return self._read_thread.is_alive()

    def stop_reader(self):
        """
        Stops the reader thread.
        """
        self._read_thread.stop()

    def close(self):
        """
        Closes the device.
        """
        try:
            self._running = False
            self._read_thread.stop()
            self._device.close()

        except:
            pass

        self.on_close()

    class ReadThread(threading.Thread):
        """
        Reader thread which processes messages from the device.
        """

        READ_TIMEOUT = 10
        """Timeout for the reader thread."""

        def __init__(self, device):
            """
            Constructor

            :param device: The device used by the reader thread.
            :type device: devices.Device
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
                    self._device.read_line(timeout=self.READ_TIMEOUT)

                except util.TimeoutError, err:
                    pass

                except Exception, err:
                    self._running = False

                    #raise err

                time.sleep(0.01)

class USBDevice(Device):
    """
    AD2USB device exposed with PyFTDI's interface.
    """

    # Constants
    FTDI_VENDOR_ID = 0x0403
    """Vendor ID used to recognize AD2USB devices."""
    FTDI_PRODUCT_ID = 0x6001
    """Product ID used to recognize AD2USB devices."""
    BAUDRATE = 115200
    """Default baudrate for AD2USB devices."""

    @staticmethod
    def find_all():
        """
        Returns all FTDI devices matching our vendor and product IDs.

        :returns: list of devices
        :raises: util.CommError
        """
        devices = []

        try:
            devices = Ftdi.find_all([(USBDevice.FTDI_VENDOR_ID, USBDevice.FTDI_PRODUCT_ID)], nocache=True)

        except (usb.core.USBError, FtdiError), err:
            raise util.CommError('Error enumerating AD2USB devices: {0}'.format(str(err)), err)

        return devices

    @property
    def interface(self):
        """
        Retrieves the interface used to connect to the device.

        :returns: the interface used to connect to the device.
        """
        return (self._device_number, self._endpoint)

    @interface.setter
    def interface(self, value):
        """
        Sets the interface used to connect to the device.

        :param value: Tuple containing the device number and endpoint number to use.
        :type value: tuple
        """
        self._device_number = value[0]
        self._endpoint = value[1]

    @property
    def serial_number(self):
        """
        Retrieves the serial number of the device.

        :returns: The serial number of the device.
        """

        return self._serial_number

    @serial_number.setter
    def serial_number(self, value):
        """
        Sets the serial number of the device.

        :param value: The serial number of the device.
        :type value: string
        """
        self._serial_number = value

    @property
    def description(self):
        """
        Retrieves the description of the device.

        :returns: The description of the device.
        """
        return self._description

    @description.setter
    def description(self, value):
        """
        Sets the description of the device.

        :param value: The description of the device.
        :type value: string
        """
        self._description = value

    def __init__(self, interface=(0, 0)):
        """
        Constructor

        :param interface: Tuple containing the device number and endpoint number to use.
        :type interface: tuple
        """
        Device.__init__(self)

        self._device = Ftdi()
        self._device_number = interface[0]
        self._endpoint = interface[1]
        self._vendor_id = USBDevice.FTDI_VENDOR_ID
        self._product_id = USBDevice.FTDI_PRODUCT_ID
        self._serial_number = None
        self._description = None

    def open(self, baudrate=BAUDRATE, no_reader_thread=False):
        """
        Opens the device.

        :param baudrate: The baudrate to use.
        :type baudrate: int
        :param no_reader_thread: Whether or not to automatically start the reader thread.
        :type no_reader_thread: bool

        :raises: util.NoDeviceError
        """
        # Set up defaults
        if baudrate is None:
            baudrate = USBDevice.BAUDRATE

        # Open the device and start up the thread.
        try:
            self._device.open(self._vendor_id,
                             self._product_id,
                             self._endpoint,
                             self._device_number,
                             self._serial_number,
                             self._description)

            self._device.set_baudrate(baudrate)

            self._id = 'USB {0}:{1}'.format(self._device.usb_dev.bus, self._device.usb_dev.address)

        except (usb.core.USBError, FtdiError), err:
            raise util.NoDeviceError('Error opening device: {0}'.format(str(err)), err)

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
            # HACK: Probably should fork pyftdi and make this call in .close().
            self._device.usb_dev.attach_kernel_driver(self._device_number)

            Device.close(self)

        except:
            pass

    def write(self, data):
        """
        Writes data to the device.

        :param data: Data to write
        :type data: str

        :raises: util.CommError
        """
        try:
            self._device.write_data(data)

            self.on_write(data)

        except FtdiError, err:
            raise util.CommError('Error writing to device: {0}'.format(str(err)), err)

    def read(self):
        """
        Reads a single character from the device.

        :returns: The character read from the device.
        :raises: util.CommError
        """
        ret = None

        try:
            ret = self._device.read_data(1)

        except (usb.core.USBError, FtdiError), err:
            raise util.CommError('Error reading from device: {0}'.format(str(err)), err)

        return ret

    def read_line(self, timeout=0.0, purge_buffer=False):
        """
        Reads a line from the device.

        :param timeout: Read timeout
        :type timeout: float
        :param purge_buffer: Indicates whether to purge the buffer prior to reading.
        :type purge_buffer: bool

        :returns: The line that was read.
        :raises: util.CommError, util.TimeoutError
        """

        if purge_buffer:
            self._buffer = ''

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

        except (usb.core.USBError, FtdiError), err:
            timer.cancel()

            raise util.CommError('Error reading from device: {0}'.format(str(err)), err)

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
    """Default baudrate for Serial devices."""

    @staticmethod
    def find_all(pattern=None):
        """
        Returns all serial ports present.

        :param pattern: Pattern to search for when retrieving serial ports.
        :type pattern: str

        :returns: list of devices
        :raises: util.CommError
        """
        devices = []

        try:
            if pattern:
                devices = serial.tools.list_ports.grep(pattern)
            else:
                devices = serial.tools.list_ports.comports()

        except SerialException, err:
            raise util.CommError('Error enumerating serial devices: {0}'.format(str(err)), err)

        return devices

    @property
    def interface(self):
        """
        Retrieves the interface used to connect to the device.

        :returns: the interface used to connect to the device.
        """
        return self._port

    @interface.setter
    def interface(self, value):
        """
        Sets the interface used to connect to the device.

        :param value: The name of the serial device.
        :type value: string
        """
        self._port = value

    def __init__(self, interface=None):
        """
        Constructor

        :param interface: The device to open.
        :type interface: str
        """
        Device.__init__(self)

        self._port = interface
        self._id = interface
        self._device = serial.Serial(timeout=0, writeTimeout=0)     # Timeout = non-blocking to match pyftdi.

    def open(self, baudrate=BAUDRATE, no_reader_thread=False):
        """
        Opens the device.

        :param baudrate: The baudrate to use with the device.
        :type baudrate: int
        :param no_reader_thread: Whether or not to automatically start the reader thread.
        :type no_reader_thread: bool

        :raises: util.NoDeviceError
        """
        # Set up the defaults
        if baudrate is None:
            baudrate = SerialDevice.BAUDRATE

        if self._port is None:
            raise util.NoDeviceError('No device interface specified.')

        self._device.port = self._port

        # Open the device and start up the reader thread.
        try:
            self._device.open()
            self._device.baudrate = baudrate            # NOTE: Setting the baudrate before opening the
                                                        #       port caused issues with Moschip 7840/7820
                                                        #       USB Serial Driver converter. (mos7840)
                                                        #
                                                        #       Moving it to this point seems to resolve
                                                        #       all issues with it.

        except (serial.SerialException, ValueError), err:
            raise util.NoDeviceError('Error opening device on port {0}.'.format(self._port), err)

        else:
            self._running = True
            self.on_open(('N/A', "AD2SERIAL"))

            if not no_reader_thread:
                self._read_thread.start()

    def close(self):
        """
        Closes the device.
        """
        try:
            Device.close(self)

        except:
            pass

    def write(self, data):
        """
        Writes data to the device.

        :param data: The data to write.
        :type data: str

        :raises: util.CommError
        """
        try:
            self._device.write(data)

        except serial.SerialTimeoutException, err:
            pass

        except serial.SerialException, err:
            raise util.CommError('Error writing to device.', err)

        else:
            self.on_write(data)

    def read(self):
        """
        Reads a single character from the device.

        :returns: The character read from the device.
        :raises: util.CommError
        """
        ret = None

        try:
            ret = self._device.read(1)

        except serial.SerialException, err:
            raise util.CommError('Error reading from device: {0}'.format(str(err)), err)

        return ret

    def read_line(self, timeout=0.0, purge_buffer=False):
        """
        Reads a line from the device.

        :param timeout: The read timeout.
        :type timeout: float
        :param purge_buffer: Indicates whether to purge the buffer prior to reading.
        :type purge_buffer: bool

        :returns: The line read.
        :raises: util.CommError, util.TimeoutError
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

        except (OSError, serial.SerialException), err:
            timer.cancel()

            raise util.CommError('Error reading from device: {0}'.format(str(err)), err)

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

    @property
    def interface(self):
        """
        Retrieves the interface used to connect to the device.

        :returns: the interface used to connect to the device.
        """
        return (self._host, self._port)

    @interface.setter
    def interface(self, value):
        """
        Sets the interface used to connect to the device.

        :param value: Tuple containing the device number and endpoint number to use.
        :type value: tuple
        """
        self._host = value[0]
        self._port = value[1]

    @property
    def ssl(self):
        """
        Retrieves whether or not the device is using SSL.

        :returns: Whether or not the device is using SSL.
        """
        return self._use_ssl

    @ssl.setter
    def ssl(self, value):
        """
        Sets whether or not SSL communication is in use.

        :param value: Whether or not SSL communication is in use.
        :type value: bool
        """
        self._use_ssl = value

    @property
    def ssl_certificate(self):
        """
        Retrieves the SSL client certificate path used for authentication.

        :returns: The certificate path
        """
        return self._ssl_certificate

    @ssl_certificate.setter
    def ssl_certificate(self, value):
        """
        Sets the SSL client certificate to use for authentication.

        :param value: The path to the SSL certificate.
        :type value: str
        """
        self._ssl_certificate = value

    @property
    def ssl_key(self):
        """
        Retrieves the SSL client certificate key used for authentication.

        :returns: The key path
        """
        return self._ssl_key

    @ssl_key.setter
    def ssl_key(self, value):
        """
        Sets the SSL client certificate key to use for authentication.

        :param value: The path to the SSL key.
        :type value: str
        """
        self._ssl_key = value

    @property
    def ssl_ca(self):
        """
        Retrieves the SSL Certificate Authority certificate used for authentication.

        :returns: The CA path
        """
        return self._ssl_ca

    @ssl_ca.setter
    def ssl_ca(self, value):
        """
        Sets the SSL Certificate Authority certificate used for authentication.

        :param value: The path to the SSL CA certificate.
        :type value: str
        """
        self._ssl_ca = value

    def __init__(self, interface=("localhost", 10000)):
        """
        Constructor

        :param interface: Tuple containing the hostname and port of our target.
        :type interface: tuple
        """
        Device.__init__(self)

        self._host, self._port = interface
        self._use_ssl = False
        self._ssl_certificate = None
        self._ssl_key = None
        self._ssl_ca = None

    def open(self, baudrate=None, no_reader_thread=False):
        """
        Opens the device.

        :param baudrate: The baudrate to use
        :type baudrate: int
        :param no_reader_thread: Whether or not to automatically open the reader thread.
        :type no_reader_thread: bool

        :raises: util.NoDeviceError, util.CommError
        """

        try:
            self._device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if self._use_ssl:
                self._init_ssl()

            self._device.connect((self._host, self._port))

            self._id = '{0}:{1}'.format(self._host, self._port)

        except socket.error, err:
            raise util.NoDeviceError('Error opening device at {0}:{1}'.format(self._host, self._port), err)

        else:
            self._running = True

            self.on_open(('N/A', "AD2SOCKET"))

            if not no_reader_thread:
                self._read_thread.start()

    def close(self):
        """
        Closes the device.
        """
        try:
            if self.ssl:
                self._device.shutdown()
            else:
                self._device.shutdown(socket.SHUT_RDWR)     # Make sure that it closes immediately.

            Device.close(self)

        except Exception, ex:
            pass

    def write(self, data):
        """
        Writes data to the device.

        :param data: The data to write.
        :type data: str

        :returns: The number of bytes sent.
        :raises: util.CommError
        """
        data_sent = None

        try:
            data_sent = self._device.send(data)

            if data_sent == 0:
                raise util.CommError('Error writing to device.')

            self.on_write(data)

        except (SSL.Error, socket.error), err:
            raise util.CommError('Error writing to device.', err)

        return data_sent

    def read(self):
        """
        Reads a single character from the device.

        :returns: The character read from the device.
        :raises: util.CommError
        """
        data = None

        try:
            data = self._device.recv(1)

        except socket.error, err:
            raise util.CommError('Error while reading from device: {0}'.format(str(err)), err)

        return data

    def read_line(self, timeout=0.0, purge_buffer=False):
        """
        Reads a line from the device.

        :param timeout: The read timeout.
        :type timeout: float
        :param purge_buffer: Indicates whether to purge the buffer prior to reading.
        :type purge_buffer: bool

        :returns: The line read from the device.
        :raises: util.CommError, util.TimeoutError
        """

        if purge_buffer:
            self._buffer = ''

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

        except socket.error, err:
            timer.cancel()

            raise util.CommError('Error reading from device: {0}'.format(str(err)), err)

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

    def _init_ssl(self):
        try:
            ctx = SSL.Context(SSL.TLSv1_METHOD)

            if isinstance(self.ssl_key, crypto.PKey):
                ctx.use_privatekey(self.ssl_key)
            else:
                ctx.use_privatekey_file(self.ssl_key)

            if isinstance(self.ssl_certificate, crypto.X509):
                ctx.use_certificate(self.ssl_certificate)
            else:
                ctx.use_certificate_file(self.ssl_certificate)

            if isinstance(self.ssl_ca, crypto.X509):
                store = ctx.get_cert_store()
                store.add_cert(self.ssl_ca)
            else:
                ctx.load_verify_locations(self.ssl_ca, None)

            ctx.set_verify(SSL.VERIFY_PEER, self._verify_ssl_callback)

            self._device = SSL.Connection(ctx, self._device)

        except SSL.Error, err:
            raise util.CommError('Error setting up SSL connection.', err)

    def _verify_ssl_callback(self, connection, x509, errnum, errdepth, ok):
        #print ok
        return ok
