"""
This module contains the :py:class:`USBDevice` interface for the `AD2USB`_.

.. _AD2USB: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import time
import threading
from .base_device import Device
from ..util import CommError, TimeoutError, NoDeviceError, bytes_hack
from ..event import event

have_pyftdi = False
try:
    from pyftdi.pyftdi.ftdi import Ftdi, FtdiError
    import usb.core
    import usb.util

    have_pyftdi = True

except ImportError:
    try:
        from pyftdi.ftdi import Ftdi, FtdiError
        import usb.core
        import usb.util

        have_pyftdi = True

    except ImportError:
        have_pyftdi = False


class USBDevice(Device):
    """
    `AD2USB`_ device utilizing PyFTDI's interface.
    """

    # Constants
    PRODUCT_IDS = ((0x0403, 0x6001), (0x0403, 0x6015))
    """List of Vendor and Product IDs used to recognize `AD2USB`_ devices."""
    DEFAULT_VENDOR_ID = PRODUCT_IDS[0][0]
    """Default Vendor ID used to recognize `AD2USB`_ devices."""
    DEFAULT_PRODUCT_ID = PRODUCT_IDS[0][1]
    """Default Product ID used to recognize `AD2USB`_ devices."""

    # Deprecated constants
    FTDI_VENDOR_ID = DEFAULT_VENDOR_ID
    """DEPRECATED: Vendor ID used to recognize `AD2USB`_ devices."""
    FTDI_PRODUCT_ID = DEFAULT_PRODUCT_ID
    """DEPRECATED: Product ID used to recognize `AD2USB`_ devices."""


    BAUDRATE = 115200
    """Default baudrate for `AD2USB`_ devices."""

    __devices = []
    __detect_thread = None

    @classmethod
    def find_all(cls, vid=None, pid=None):
        """
        Returns all FTDI devices matching our vendor and product IDs.

        :returns: list of devices
        :raises: :py:class:`~alarmdecoder.util.CommError`
        """
        if not have_pyftdi:
            raise ImportError('The USBDevice class has been disabled due to missing requirement: pyftdi or pyusb.')

        cls.__devices = []

        query = cls.PRODUCT_IDS
        if vid and pid:
            query = [(vid, pid)]

        try:
            cls.__devices = Ftdi.find_all(query, nocache=True)

        except (usb.core.USBError, FtdiError) as err:
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
        if not have_pyftdi:
            raise ImportError('The USBDevice class has been disabled due to missing requirement: pyftdi or pyusb.')

        cls.find_all()

        if len(cls.__devices) == 0:
            raise NoDeviceError('No AD2USB devices present.')

        if device is None:
            device = cls.__devices[0]

        vendor, product, sernum, ifcount, description = device

        return USBDevice(interface=sernum, vid=vendor, pid=product)

    @classmethod
    def start_detection(cls, on_attached=None, on_detached=None):
        """
        Starts the device detection thread.

        :param on_attached: function to be called when a device is attached  **Callback definition:** *def callback(thread, device)*
        :type on_attached: function
        :param on_detached: function to be called when a device is detached  **Callback definition:** *def callback(thread, device)*

        :type on_detached: function
        """
        if not have_pyftdi:
            raise ImportError('The USBDevice class has been disabled due to missing requirement: pyftdi or pyusb.')

        cls.__detect_thread = USBDevice.DetectThread(on_attached, on_detached)

        try:
            cls.find_all()
        except CommError:
            pass

        cls.__detect_thread.start()

    @classmethod
    def stop_detection(cls):
        """
        Stops the device detection thread.
        """
        if not have_pyftdi:
            raise ImportError('The USBDevice class has been disabled due to missing requirement: pyftdi or pyusb.')

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

    def __init__(self, interface=0, vid=None, pid=None):
        """
        Constructor

        :param interface: May specify either the serial number or the device
                          index.
        :type interface: string or int
        """
        if not have_pyftdi:
            raise ImportError('The USBDevice class has been disabled due to missing requirement: pyftdi or pyusb.')

        Device.__init__(self)

        self._device = Ftdi()

        self._interface = 0
        self._device_number = 0
        self._serial_number = None

        self._vendor_id = USBDevice.DEFAULT_VENDOR_ID
        if vid:
            self._vendor_id = vid

        self._product_id = USBDevice.DEFAULT_PRODUCT_ID
        if pid:
            self._product_id = pid

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

        self._read_thread = Device.ReadThread(self)

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

        except (usb.core.USBError, FtdiError) as err:
            raise NoDeviceError('Error opening device: {0}'.format(str(err)), err)

        except KeyError as err:
            raise NoDeviceError('Unsupported device. ({0:04x}:{1:04x})  You probably need a newer version of pyftdi.'.format(err[0][0], err[0][1]))

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

    def fileno(self):
        """
        File number not supported for USB devices.
    
        :raises: NotImplementedError
        """
        raise NotImplementedError('USB devices do not support fileno()')

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

        except FtdiError as err:
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

        except (usb.core.USBError, FtdiError) as err:
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
            self._buffer = b''

        got_line, ret = False, None

        timer = threading.Timer(timeout, timeout_event)
        if timeout > 0:
            timer.start()

        try:
            while timeout_event.reading:
                buf = self._device.read_data(1)

                if buf != b'':
                    ub = bytes_hack(buf)

                    self._buffer += ub

                    if ub == b"\n":
                        self._buffer = self._buffer.rstrip(b"\r\n")

                        if len(self._buffer) > 0:
                            got_line = True
                            break
                else:
                    time.sleep(0.01)

        except (usb.core.USBError, FtdiError) as err:
            raise CommError('Error reading from device: {0}'.format(str(err)), err)

        else:
            if got_line:
                ret, self._buffer = self._buffer, b''

                self.on_read(data=ret)

            else:
                raise TimeoutError('Timeout while waiting for line terminator.')

        finally:
            timer.cancel()

        return ret

    def purge(self):
        """
        Purges read/write buffers.
        """
        self._device.purge_buffers()

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