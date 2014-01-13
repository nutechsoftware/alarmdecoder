"""
This module contains different types of devices belonging to the `AlarmDecoder`_ (AD2) family.

* :py:class:`USBDevice`: Interfaces with the `AD2USB`_ device.
* :py:class:`SerialDevice`: Interfaces with the `AD2USB`_, `AD2SERIAL`_ or `AD2PI`_.
* :py:class:`SocketDevice`: Interfaces with devices exposed through `ser2sock`_ or another IP to Serial solution.
  Also supports SSL if using `ser2sock`_.

.. _ser2sock: http://github.com/nutechsoftware/ser2sock
.. _AlarmDecoder: http://www.alarmdecoder.com
.. _AD2USB: http://www.alarmdecoder.com
.. _AD2SERIAL: http://www.alarmdecoder.com
.. _AD2PI: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import usb.core
import usb.util
import time
import threading
import serial
import serial.tools.list_ports
import socket

from OpenSSL import SSL, crypto
from pyftdi.pyftdi.ftdi import Ftdi, FtdiError
from .util import CommError, TimeoutError, NoDeviceError
from .event import event


class Device(object):
    """
    Base class for all `AlarmDecoder`_ (AD2) device types.
    """

    # Generic device events
    on_open = event.Event("This event is called when the device has been opened.\n\n**Callback definition:** *def callback(device)*")
    on_close = event.Event("This event is called when the device has been closed.\n\n**Callback definition:** def callback(device)*")
    on_read = event.Event("This event is called when a line has been read from the device.\n\n**Callback definition:** def callback(device, data)*")
    on_write = event.Event("This event is called when data has been written to the device.\n\n**Callback definition:** def callback(device, data)*")

    def __init__(self):
        """
        Constructor
        """
        self._id = ''
        self._buffer = ''
        self._device = None
        self._running = False
        self._read_thread = Device.ReadThread(self)

    def __enter__(self):
        """
        Support for context manager __enter__.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Support for context manager __exit__.
        """
        self.close()

        return False

    @property
    def id(self):
        """
        Retrieve the device ID.

        :returns: identification string for the device
        """
        return self._id

    @id.setter
    def id(self, value):
        """
        Sets the device ID.

        :param value: device identification string
        :type value: string
        """
        self._id = value

    def is_reader_alive(self):
        """
        Indicates whether or not the reader thread is alive.

        :returns: whether or not the reader thread is alive
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

        except Exception:
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

            :param device: device used by the reader thread
            :type device: :py:class:`~alarmdecoder.devices.Device`
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

                except TimeoutError:
                    pass

                except Exception:
                    self._running = False


class USBDevice(Device):
    """
    `AD2USB`_ device utilizing PyFTDI's interface.
    """

    # Constants
    FTDI_VENDOR_ID = 0x0403
    """Vendor ID used to recognize `AD2USB`_ devices."""
    FTDI_PRODUCT_ID = 0x6001
    """Product ID used to recognize `AD2USB`_ devices."""
    BAUDRATE = 115200
    """Default baudrate for `AD2USB`_ devices."""

    __devices = []
    __detect_thread = None

    @classmethod
    def find_all(cls, vid=FTDI_VENDOR_ID, pid=FTDI_PRODUCT_ID):
        """
        Returns all FTDI devices matching our vendor and product IDs.

        :returns: list of devices
        :raises: :py:class:`~alarmdecoder.util.CommError`
        """
        cls.__devices = []

        try:
            cls.__devices = Ftdi.find_all([(vid, pid)], nocache=True)

        except (usb.core.USBError, FtdiError), err:
            raise CommError('Error enumerating AD2USB devices: {0}'.format(str(err)), err)

        return cls.__devices

    @classmethod
    def devices(cls):
        """
        Returns a cached list of `AD2USB`_ devices located on the system.

        :returns: cached list of devices found
        """
        return cls.__devices

    @classmethod
    def find(cls, device=None):
        """
        Factory method that returns the requested :py:class:`USBDevice` device, or the
        first device.

        :param device: Tuple describing the USB device to open, as returned
                       by find_all().
        :type device: tuple

        :returns: :py:class:`USBDevice` object utilizing the specified device
        :raises: :py:class:`~alarmdecoder.util.NoDeviceError`
        """
        cls.find_all()

        if len(cls.__devices) == 0:
            raise NoDeviceError('No AD2USB devices present.')

        if device is None:
            device = cls.__devices[0]

        vendor, product, sernum, ifcount, description = device

        return USBDevice(interface=sernum)

    @classmethod
    def start_detection(cls, on_attached=None, on_detached=None):
        """
        Starts the device detection thread.

        :param on_attached: function to be called when a device is attached  **Callback definition:** *def callback(thread, device)*
        :type on_attached: function
        :param on_detached: function to be called when a device is detached  **Callback definition:** *def callback(thread, device)*

        :type on_detached: function
        """
        cls.__detect_thread = USBDevice.DetectThread(on_attached, on_detached)

        cls.find_all()

        cls.__detect_thread.start()

    @classmethod
    def stop_detection(cls):
        """
        Stops the device detection thread.
        """
        try:
            cls.__detect_thread.stop()

        except Exception:
            pass

    @property
    def interface(self):
        """
        Retrieves the interface used to connect to the device.

        :returns: the interface used to connect to the device
        """
        return self._interface

    @interface.setter
    def interface(self, value):
        """
        Sets the interface used to connect to the device.

        :param value: may specify either the serial number or the device index
        :type value: string or int
        """
        self._interface = value
        if isinstance(value, int):
            self._device_number = value
        else:
            self._serial_number = value

    @property
    def serial_number(self):
        """
        Retrieves the serial number of the device.

        :returns: serial number of the device
        """

        return self._serial_number

    @serial_number.setter
    def serial_number(self, value):
        """
        Sets the serial number of the device.

        :param value: serial number of the device
        :type value: string
        """
        self._serial_number = value

    @property
    def description(self):
        """
        Retrieves the description of the device.

        :returns: description of the device
        """
        return self._description

    @description.setter
    def description(self, value):
        """
        Sets the description of the device.

        :param value: description of the device
        :type value: string
        """
        self._description = value

    def __init__(self, interface=0):
        """
        Constructor

        :param interface: May specify either the serial number or the device
                          index.
        :type interface: string or int
        """
        Device.__init__(self)

        self._device = Ftdi()

        self._interface = 0
        self._device_number = 0
        self._serial_number = None
        self._vendor_id = USBDevice.FTDI_VENDOR_ID
        self._product_id = USBDevice.FTDI_PRODUCT_ID
        self._endpoint = 0
        self._description = None

        self.interface = interface

    def open(self, baudrate=BAUDRATE, no_reader_thread=False):
        """
        Opens the device.

        :param baudrate: baudrate to use
        :type baudrate: int
        :param no_reader_thread: whether or not to automatically start the
                                 reader thread.
        :type no_reader_thread: bool

        :raises: :py:class:`~alarmdecoder.util.NoDeviceError`
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

            if not self._serial_number:
                self._serial_number = self._get_serial_number()

            self._id = self._serial_number

        except (usb.core.USBError, FtdiError), err:
            raise NoDeviceError('Error opening device: {0}'.format(str(err)), err)

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

            # HACK: Probably should fork pyftdi and make this call in .close()
            self._device.usb_dev.attach_kernel_driver(self._device_number)

        except Exception:
            pass

    def write(self, data):
        """
        Writes data to the device.

        :param data: data to write
        :type data: string

        :raises: :py:class:`~alarmdecoder.util.CommError`
        """
        try:
            self._device.write_data(data)

            self.on_write(data=data)

        except FtdiError, err:
            raise CommError('Error writing to device: {0}'.format(str(err)), err)

    def read(self):
        """
        Reads a single character from the device.

        :returns: character read from the device
        :raises: :py:class:`~alarmdecoder.util.CommError`
        """
        ret = None

        try:
            ret = self._device.read_data(1)

        except (usb.core.USBError, FtdiError), err:
            raise CommError('Error reading from device: {0}'.format(str(err)), err)

        return ret

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
            self._buffer = ''

        got_line, ret = False, None

        timer = threading.Timer(timeout, timeout_event)
        if timeout > 0:
            timer.start()

        try:
            while timeout_event.reading:
                buf = self._device.read_data(1)

                if buf != '':
                    self._buffer += buf

                    if buf == "\n":
                        self._buffer = self._buffer.rstrip("\r\n")

                        if len(self._buffer) > 0:
                            got_line = True
                            break
                else:
                    time.sleep(0.01)

        except (usb.core.USBError, FtdiError), err:
            raise CommError('Error reading from device: {0}'.format(str(err)), err)

        else:
            if got_line:
                ret, self._buffer = self._buffer, ''

                self.on_read(data=ret)

            else:
                raise TimeoutError('Timeout while waiting for line terminator.')

        finally:
            timer.cancel()

        return ret

    def _get_serial_number(self):
        """
        Retrieves the FTDI device serial number.

        :returns: string containing the device serial number
        """
        return usb.util.get_string(self._device.usb_dev, 64, self._device.usb_dev.iSerialNumber)

    class DetectThread(threading.Thread):
        """
        Thread that handles detection of added/removed devices.
        """
        on_attached = event.Event("This event is called when an `AD2USB`_ device has been detected.\n\n**Callback definition:** def callback(thread, device*")
        on_detached = event.Event("This event is called when an `AD2USB`_ device has been removed.\n\n**Callback definition:** def callback(thread, device*")

        def __init__(self, on_attached=None, on_detached=None):
            """
            Constructor

            :param on_attached: Function to call when a device is attached  **Callback definition:** *def callback(thread, device)*
            :type on_attached: function
            :param on_detached: Function to call when a device is detached  **Callback definition:** *def callback(thread, device)*
            :type on_detached: function
            """
            threading.Thread.__init__(self)

            if on_attached:
                self.on_attached += on_attached

            if on_detached:
                self.on_detached += on_detached

            self._running = False

        def stop(self):
            """
            Stops the thread.
            """
            self._running = False

        def run(self):
            """
            The actual detection process.
            """
            self._running = True

            last_devices = set()

            while self._running:
                try:
                    current_devices = set(USBDevice.find_all())

                    for dev in current_devices.difference(last_devices):
                        self.on_attached(device=dev)

                    for dev in last_devices.difference(current_devices):
                        self.on_detached(device=dev)

                    last_devices = current_devices

                except CommError:
                    pass

                time.sleep(0.25)


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

        except serial.SerialException, err:
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

        except (serial.SerialException, ValueError), err:
            raise NoDeviceError('Error opening device on port {0}.'.format(self._port), err)

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

    def write(self, data):
        """
        Writes data to the device.

        :param data: data to write
        :type data: string

        :raises: py:class:`~alarmdecoder.util.CommError`
        """
        try:
            self._device.write(data)

        except serial.SerialTimeoutException:
            pass

        except serial.SerialException, err:
            raise CommError('Error writing to device.', err)

        else:
            self.on_write(data=data)

    def read(self):
        """
        Reads a single character from the device.

        :returns: character read from the device
        :raises: :py:class:`~alarmdecoder.util.CommError`
        """
        ret = None

        try:
            ret = self._device.read(1)

        except serial.SerialException, err:
            raise CommError('Error reading from device: {0}'.format(str(err)), err)

        return ret

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
            self._buffer = ''

        got_line, ret = False, None

        timer = threading.Timer(timeout, timeout_event)
        if timeout > 0:
            timer.start()

        try:
            while timeout_event.reading:
                buf = self._device.read(1)

                # NOTE: AD2SERIAL apparently sends down \xFF on boot.
                if buf != '' and buf != "\xff":
                    self._buffer += buf

                    if buf == "\n":
                        self._buffer = self._buffer.rstrip("\r\n")

                        if len(self._buffer) > 0:
                            got_line = True
                            break
                else:
                    time.sleep(0.01)

        except (OSError, serial.SerialException), err:
            raise CommError('Error reading from device: {0}'.format(str(err)), err)

        else:
            if got_line:
                ret, self._buffer = self._buffer, ''

                self.on_read(data=ret)

            else:
                raise TimeoutError('Timeout while waiting for line terminator.')

        finally:
            timer.cancel()

        return ret


class SocketDevice(Device):
    """
    Device that supports communication with an `AlarmDecoder`_ (AD2) that is
    exposed via `ser2sock`_ or another Serial to IP interface.
    """

    @property
    def interface(self):
        """
        Retrieves the interface used to connect to the device.

        :returns: interface used to connect to the device
        """
        return (self._host, self._port)

    @interface.setter
    def interface(self, value):
        """
        Sets the interface used to connect to the device.

        :param value: Tuple containing the host and port to use
        :type value: tuple
        """
        self._host, self._port = value

    @property
    def ssl(self):
        """
        Retrieves whether or not the device is using SSL.

        :returns: whether or not the device is using SSL
        """
        return self._use_ssl

    @ssl.setter
    def ssl(self, value):
        """
        Sets whether or not SSL communication is in use.

        :param value: Whether or not SSL communication is in use
        :type value: bool
        """
        self._use_ssl = value

    @property
    def ssl_certificate(self):
        """
        Retrieves the SSL client certificate path used for authentication.

        :returns: path to the certificate path or :py:class:`OpenSSL.crypto.X509`
        """
        return self._ssl_certificate

    @ssl_certificate.setter
    def ssl_certificate(self, value):
        """
        Sets the SSL client certificate to use for authentication.

        :param value: path to the SSL certificate or :py:class:`OpenSSL.crypto.X509`
        :type value: string or :py:class:`OpenSSL.crypto.X509`
        """
        self._ssl_certificate = value

    @property
    def ssl_key(self):
        """
        Retrieves the SSL client certificate key used for authentication.

        :returns: jpath to the SSL key or :py:class:`OpenSSL.crypto.PKey`
        """
        return self._ssl_key

    @ssl_key.setter
    def ssl_key(self, value):
        """
        Sets the SSL client certificate key to use for authentication.

        :param value: path to the SSL key or :py:class:`OpenSSL.crypto.PKey`
        :type value: string or :py:class:`OpenSSL.crypto.PKey`
        """
        self._ssl_key = value

    @property
    def ssl_ca(self):
        """
        Retrieves the SSL Certificate Authority certificate used for
        authentication.

        :returns: path to the CA certificate or :py:class:`OpenSSL.crypto.X509`
        """
        return self._ssl_ca

    @ssl_ca.setter
    def ssl_ca(self, value):
        """
        Sets the SSL Certificate Authority certificate used for authentication.

        :param value: path to the SSL CA certificate or :py:class:`OpenSSL.crypto.X509`
        :type value: string or :py:class:`OpenSSL.crypto.X509`
        """
        self._ssl_ca = value

    def __init__(self, interface=("localhost", 10000)):
        """
        Constructor

        :param interface: Tuple containing the hostname and port of our target
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

        :param baudrate: baudrate to use
        :type baudrate: int
        :param no_reader_thread: whether or not to automatically open the reader
                                 thread.
        :type no_reader_thread: bool

        :raises: :py:class:`~alarmdecoder.util.NoDeviceError`, :py:class:`~alarmdecoder.util.CommError`
        """

        try:
            self._device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if self._use_ssl:
                self._init_ssl()

            self._device.connect((self._host, self._port))

            if self._use_ssl:
                self._device.do_handshake()

            self._id = '{0}:{1}'.format(self._host, self._port)

        except socket.error, err:
            raise NoDeviceError('Error opening device at {0}:{1}'.format(self._host, self._port), err)

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
            # TODO: Find a way to speed up this shutdown.
            if self.ssl:
                self._device.shutdown()

            else:
                # Make sure that it closes immediately.
                self._device.shutdown(socket.SHUT_RDWR)

            Device.close(self)

        except Exception:
            pass

    def write(self, data):
        """
        Writes data to the device.

        :param data: data to write
        :type data: string

        :returns: number of bytes sent
        :raises: :py:class:`~alarmdecoder.util.CommError`
        """
        data_sent = None

        try:
            data_sent = self._device.send(data)

            if data_sent == 0:
                raise CommError('Error writing to device.')

            self.on_write(data=data)

        except (SSL.Error, socket.error), err:
            raise CommError('Error writing to device.', err)

        return data_sent

    def read(self):
        """
        Reads a single character from the device.

        :returns: character read from the device
        :raises: :py:class:`~alarmdecoder.util.CommError`
        """
        data = None

        try:
            data = self._device.recv(1)

        except socket.error, err:
            raise CommError('Error while reading from device: {0}'.format(str(err)), err)

        return data

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
            self._buffer = ''

        got_line, ret = False, None

        timer = threading.Timer(timeout, timeout_event)
        if timeout > 0:
            timer.start()

        try:
            while timeout_event.reading:
                buf = self._device.recv(1)

                if buf != '':
                    self._buffer += buf

                    if buf == "\n":
                        self._buffer = self._buffer.rstrip("\r\n")

                        if len(self._buffer) > 0:
                            got_line = True
                            break
                else:
                    time.sleep(0.01)

        except socket.error, err:
            raise CommError('Error reading from device: {0}'.format(str(err)), err)

        else:
            if got_line:
                ret, self._buffer = self._buffer, ''

                self.on_read(data=ret)

            else:
                raise TimeoutError('Timeout while waiting for line terminator.')

        finally:
            timer.cancel()

        return ret

    def _init_ssl(self):
        """
        Initializes our device as an SSL connection.

        :raises: :py:class:`~alarmdecoder.util.CommError`
        """

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
            raise CommError('Error setting up SSL connection.', err)

    def _verify_ssl_callback(self, connection, x509, errnum, errdepth, ok):
        """
        SSL verification callback.
        """
        return ok
