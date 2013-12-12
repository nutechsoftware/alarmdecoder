from unittest import TestCase
from mock import Mock, MagicMock, patch
from serial import Serial, SerialException
from pyftdi.pyftdi.ftdi import Ftdi, FtdiError
from usb.core import USBError, Device as USBCoreDevice
import socket
import time
import tempfile
import os
from OpenSSL import SSL, crypto
from alarmdecoder.devices import USBDevice, SerialDevice, SocketDevice
from alarmdecoder.util import NoDeviceError, CommError, TimeoutError


class TestUSBDevice(TestCase):
    def setUp(self):
        self._device = USBDevice()
        self._device._device = Mock(spec=Ftdi)
        self._device._device.usb_dev = Mock(spec=USBCoreDevice)
        self._device._device.usb_dev.bus = 0
        self._device._device.usb_dev.address = 0

        self._attached = False
        self._detached = False

    def tearDown(self):
        self._device.close()

    def attached_event(self, sender, *args, **kwargs):
        self._attached = True

    def detached_event(self, sender, *args, **kwargs):
        self._detached = True

    def test_find_default_param(self):
        with patch.object(Ftdi, 'find_all', return_value=[(0, 0, 'AD2', 1, 'AD2')]):
            device = USBDevice.find()

            self.assertEquals(device.interface, 'AD2')

    def test_find_with_param(self):
        with patch.object(Ftdi, 'find_all', return_value=[(0, 0, 'AD2-1', 1, 'AD2'), (0, 0, 'AD2-2', 1, 'AD2')]):
            device = USBDevice.find((0, 0, 'AD2-1', 1, 'AD2'))
            self.assertEquals(device.interface, 'AD2-1')

            device = USBDevice.find((0, 0, 'AD2-2', 1, 'AD2'))
            self.assertEquals(device.interface, 'AD2-2')

    def test_events(self):
        self.assertEquals(self._attached, False)
        self.assertEquals(self._detached, False)

        # this is ugly, but it works.
        with patch.object(USBDevice, 'find_all', return_value=[(0, 0, 'AD2-1', 1, 'AD2'), (0, 0, 'AD2-2', 1, 'AD2')]):
            USBDevice.start_detection(on_attached=self.attached_event, on_detached=self.detached_event)

            with patch.object(USBDevice, 'find_all', return_value=[(0, 0, 'AD2-2', 1, 'AD2')]):
                USBDevice.find_all()
                time.sleep(1)
                USBDevice.stop_detection()

        self.assertEquals(self._attached, True)
        self.assertEquals(self._detached, True)

    def test_find_all(self):
        with patch.object(USBDevice, 'find_all', return_value=[]) as mock:
            devices = USBDevice.find_all()

        self.assertEquals(devices, [])

    def test_find_all_exception(self):
        with patch.object(Ftdi, 'find_all', side_effect=[USBError('testing'), FtdiError]) as mock:
            with self.assertRaises(CommError):
                devices = USBDevice.find_all()

            with self.assertRaises(CommError):
                devices = USBDevice.find_all()

    def test_interface_serial_number(self):
        self._device.interface = 'AD2USB'

        self.assertEquals(self._device.interface, 'AD2USB')
        self.assertEquals(self._device.serial_number, 'AD2USB')
        self.assertEquals(self._device._device_number, 0)

    def test_interface_index(self):
        self._device.interface = 1

        self.assertEquals(self._device.interface, 1)
        self.assertEquals(self._device.serial_number, None)
        self.assertEquals(self._device._device_number, 1)

    def test_open(self):
        self._device.interface = 'AD2USB'

        with patch.object(self._device._device, 'open') as mock:
            self._device.open(no_reader_thread=True)

            mock.assert_any_calls()

    def test_open_failed(self):
        self._device.interface = 'AD2USB'

        with patch.object(self._device._device, 'open', side_effect=[USBError('testing'), FtdiError]):
            with self.assertRaises(NoDeviceError):
                self._device.open(no_reader_thread=True)

            with self.assertRaises(NoDeviceError):
                self._device.open(no_reader_thread=True)

    def test_write(self):
        self._device.interface = 'AD2USB'
        self._device.open(no_reader_thread=True)

        with patch.object(self._device._device, 'write_data') as mock:
            self._device.write('test')

            mock.assert_called_with('test')

    def test_write_exception(self):
        with patch.object(self._device._device, 'write_data', side_effect=FtdiError):
            with self.assertRaises(CommError):
                self._device.write('test')

    def test_read(self):
        self._device.interface = 'AD2USB'
        self._device.open(no_reader_thread=True)

        with patch.object(self._device._device, 'read_data') as mock:
            self._device.read()

            mock.assert_called_with(1)

    def test_read_exception(self):
        with patch.object(self._device._device, 'read_data', side_effect=[USBError('testing'), FtdiError]):
            with self.assertRaises(CommError):
                self._device.read()

            with self.assertRaises(CommError):
                self._device.read()

    def test_read_line(self):
        with patch.object(self._device._device, 'read_data', side_effect=list("testing\r\n")):
            ret = None
            try:
                ret = self._device.read_line()
            except StopIteration:
                pass

            self.assertEquals(ret, "testing")

    def test_read_line_timeout(self):
        with patch.object(self._device._device, 'read_data', return_value='a') as mock:
            with self.assertRaises(TimeoutError):
                self._device.read_line(timeout=0.1)

        self.assertIn('a', self._device._buffer)

    def test_read_line_exception(self):
        with patch.object(self._device._device, 'read_data', side_effect=[USBError('testing'), FtdiError]):
            with self.assertRaises(CommError):
                self._device.read_line()

            with self.assertRaises(CommError):
                self._device.read_line()


class TestSerialDevice(TestCase):
    def setUp(self):
        self._device = SerialDevice()
        self._device._device = Mock(spec=Serial)
        self._device._device.open = Mock()

    def tearDown(self):
        self._device.close()

    def test_open(self):
        self._device.interface = '/dev/ttyS0'

        with patch.object(self._device._device, 'open') as mock:
            self._device.open(no_reader_thread=True)

            mock.assert_called_with()

    def test_open_no_interface(self):
        with self.assertRaises(NoDeviceError):
            self._device.open(no_reader_thread=True)

        self.assertFalse(self._device._running)

    def test_open_failed(self):
        self._device.interface = '/dev/ttyS0'

        with patch.object(self._device._device, 'open', side_effect=[SerialException, ValueError]):
            with self.assertRaises(NoDeviceError):
                self._device.open(no_reader_thread=True)

            with self.assertRaises(NoDeviceError):
                self._device.open(no_reader_thread=True)

    def test_write(self):
        self._device.interface = '/dev/ttyS0'
        self._device.open(no_reader_thread=True)

        with patch.object(self._device._device, 'write') as mock:
            self._device.write('test')

            mock.assert_called_with('test')

    def test_write_exception(self):
        with patch.object(self._device._device, 'write', side_effect=SerialException):
            with self.assertRaises(CommError):
                self._device.write('test')

    def test_read(self):
        self._device.interface = '/dev/ttyS0'
        self._device.open(no_reader_thread=True)

        with patch.object(self._device._device, 'read') as mock:
            self._device.read()

            mock.assert_called_with(1)

    def test_read_exception(self):
        with patch.object(self._device._device, 'read', side_effect=SerialException):
            with self.assertRaises(CommError):
                self._device.read()

    def test_read_line(self):
        with patch.object(self._device._device, 'read', side_effect=list("testing\r\n")):
            ret = None
            try:
                ret = self._device.read_line()
            except StopIteration:
                pass

            self.assertEquals(ret, "testing")

    def test_read_line_timeout(self):
        with patch.object(self._device._device, 'read', return_value='a') as mock:
            with self.assertRaises(TimeoutError):
                self._device.read_line(timeout=0.1)

        self.assertIn('a', self._device._buffer)

    def test_read_line_exception(self):
        with patch.object(self._device._device, 'read', side_effect=[OSError, SerialException]):
            with self.assertRaises(CommError):
                self._device.read_line()

            with self.assertRaises(CommError):
                self._device.read_line()


class TestSocketDevice(TestCase):
    def setUp(self):
        self._device = SocketDevice()
        self._device._device = Mock(spec=socket.socket)

    def tearDown(self):
        self._device.close()

    def test_open(self):
        with patch.object(socket.socket, '__init__', return_value=None):
            with patch.object(socket.socket, 'connect', return_value=None) as mock:
                self._device.open(no_reader_thread=True)

        mock.assert_called_with(self._device.interface)

    def test_open_failed(self):
        with patch.object(socket.socket, 'connect', side_effect=socket.error):
            with self.assertRaises(NoDeviceError):
                self._device.open(no_reader_thread=True)

    def test_write(self):
        with patch.object(socket.socket, '__init__', return_value=None):
            with patch.object(socket.socket, 'connect', return_value=None):
                self._device.open(no_reader_thread=True)

            with patch.object(socket.socket, 'send') as mock:
                self._device.write('test')

            mock.assert_called_with('test')

    def test_write_exception(self):
        with patch.object(self._device._device, 'send', side_effect=[SSL.Error, socket.error]):
            with self.assertRaises(CommError):
                self._device.write('test')

    def test_read(self):
        with patch.object(socket.socket, '__init__', return_value=None):
            with patch.object(socket.socket, 'connect', return_value=None):
                self._device.open(no_reader_thread=True)

            with patch.object(socket.socket, 'recv') as mock:
                self._device.read()

            mock.assert_called_with(1)

    def test_read_exception(self):
        with patch.object(self._device._device, 'recv', side_effect=socket.error):
            with self.assertRaises(CommError):
                self._device.read()

    def test_read_line(self):
        with patch.object(self._device._device, 'recv', side_effect=list("testing\r\n")):
            ret = None
            try:
                ret = self._device.read_line()
            except StopIteration:
                pass

            self.assertEquals(ret, "testing")

    def test_read_line_timeout(self):
        with patch.object(self._device._device, 'recv', return_value='a') as mock:
            with self.assertRaises(TimeoutError):
                self._device.read_line(timeout=0.1)

        self.assertIn('a', self._device._buffer)

    def test_read_line_exception(self):
        with patch.object(self._device._device, 'recv', side_effect=socket.error):
            with self.assertRaises(CommError):
                self._device.read_line()

            with self.assertRaises(CommError):
                self._device.read_line()

    def test_ssl(self):
        ssl_key = crypto.PKey()
        ssl_key.generate_key(crypto.TYPE_RSA, 2048)
        ssl_cert = crypto.X509()
        ssl_cert.set_pubkey(ssl_key)
        ssl_ca_key = crypto.PKey()
        ssl_ca_key.generate_key(crypto.TYPE_RSA, 2048)
        ssl_ca_cert = crypto.X509()
        ssl_ca_cert.set_pubkey(ssl_ca_key)

        self._device.ssl = True
        self._device.ssl_key = ssl_key
        self._device.ssl_certificate = ssl_cert
        self._device.ssl_ca = ssl_ca_cert

        fileno, path = tempfile.mkstemp()

        # ..there has to be a better way..
        with patch.object(socket.socket, '__init__', return_value=None):
            with patch.object(socket.socket, 'connect', return_value=None) as mock:
                with patch.object(socket.socket, '_sock'):
                    with patch.object(socket.socket, 'fileno', return_value=fileno):
                        try:
                            self._device.open(no_reader_thread=True)
                        except SSL.SysCallError, ex:
                            pass

        os.close(fileno)
        os.unlink(path)

        mock.assert_called_with(self._device.interface)
        self.assertIsInstance(self._device._device, SSL.Connection)

    def test_ssl_exception(self):
        self._device.ssl = True
        self._device.ssl_key = 'None'
        self._device.ssl_certificate = 'None'
        self._device.ssl_ca = 'None'

        fileno, path = tempfile.mkstemp()

        # ..there has to be a better way..
        with patch.object(socket.socket, '__init__', return_value=None):
            with patch.object(socket.socket, 'connect', return_value=None) as mock:
                with patch.object(socket.socket, '_sock'):
                    with patch.object(socket.socket, 'fileno', return_value=fileno):
                        with self.assertRaises(CommError):
                            try:
                                self._device.open(no_reader_thread=True)
                            except SSL.SysCallError, ex:
                                pass

        os.close(fileno)
        os.unlink(path)
