"""
This module contains :py:class:`SocketDevice` interface for `AlarmDecoder`_ devices
that are exposed through `ser2sock`_ or another IP to serial solution.  Also supports
SSL if using `ser2sock`_.

.. _ser2sock: http://github.com/nutechsoftware/ser2sock
.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import threading
import socket
import select
from .base_device import Device
from ..util import CommError, TimeoutError, NoDeviceError, bytes_hack

try:
    from OpenSSL import SSL, crypto

    have_openssl = True

except ImportError:
    class SSL:
        class Error(BaseException):
            pass

        class WantReadError(BaseException):
            pass

        class SysCallError(BaseException):
            pass

    have_openssl = False


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

    @property
    def ssl_allow_self_signed(self):
        """
        Retrieves whether this socket is to allow self signed SSL certificates.

        :returns: True if self signed certificates are allowed, otherwise False
        """
        return self._ssl_allow_self_signed

    @ssl_allow_self_signed.setter
    def ssl_allow_self_signed(self, value):
        """
        Sets whether this socket is to allow self signed SSL certificates.

        :param value: True if self signed certificates are to be allowed, otherwise False (or don't set it at all)
        :type value: bool
        """
        self._ssl_allow_self_signed = value

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
        self._ssl_allow_self_signed = False

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
            self._read_thread = Device.ReadThread(self)

            self._device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if self._use_ssl:
                self._init_ssl()

            self._device.connect((self._host, self._port))

            if self._use_ssl:
                while True:
                    try:
                        self._device.do_handshake()
                        break
                    except SSL.WantReadError:
                        pass

            self._id = '{0}:{1}'.format(self._host, self._port)

        except socket.error as err:
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

        except Exception:
            pass

        Device.close(self)

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

        :returns: number of bytes sent
        :raises: :py:class:`~alarmdecoder.util.CommError`
        """
        data_sent = None

        try:
            if isinstance(data, str):
                data = data.encode('utf-8')

            data_sent = self._device.send(data)

            if data_sent == 0:
                raise CommError('Error writing to device.')

            self.on_write(data=data)

        except (SSL.Error, socket.error) as err:
            raise CommError('Error writing to device.', err)

        return data_sent

    def read(self):
        """
        Reads a single character from the device.

        :returns: character read from the device
        :raises: :py:class:`~alarmdecoder.util.CommError`
        """
        data = ''

        try:
            read_ready, _, _ = select.select([self._device], [], [], 0.5)

            if len(read_ready) != 0:
                data = self._device.recv(1)

        except socket.error as err:
            raise CommError('Error while reading from device: {0}'.format(str(err)), err)

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
                read_ready, _, _ = select.select([self._device], [], [], 0.5)

                if len(read_ready) == 0:
                    continue

                buf = self._device.recv(1)

                if buf != b'' and buf != b"\xff":
                    ub = bytes_hack(buf)

                    self._buffer += ub

                    if ub == b"\n":
                        self._buffer = self._buffer.rstrip(b"\r\n")

                        if len(self._buffer) > 0:
                            got_line = True
                            break

        except socket.error as err:
            raise CommError('Error reading from device: {0}'.format(str(err)), err)

        except SSL.SysCallError as err:
            errno, msg = err
            raise CommError('SSL error while reading from device: {0} ({1})'.format(msg, errno))

        except Exception:
            raise

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
        try:
            self._device.setblocking(0)
            while(self._device.recv(1)):
                pass
        except socket.error as err:
            pass
        finally:
            self._device.setblocking(1)

    def _init_ssl(self):
        """
        Initializes our device as an SSL connection.

        :raises: :py:class:`~alarmdecoder.util.CommError`
        """

        if not have_openssl:
            raise ImportError('SSL sockets have been disabled due to missing requirement: pyopenssl.')

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

            verify_method = SSL.VERIFY_PEER
            if (self._ssl_allow_self_signed):
                verify_method = SSL.VERIFY_NONE

            ctx.set_verify(verify_method, self._verify_ssl_callback)

            self._device = SSL.Connection(ctx, self._device)

        except SSL.Error as err:
            raise CommError('Error setting up SSL connection.', err)

    def _verify_ssl_callback(self, connection, x509, errnum, errdepth, ok):
        """
        SSL verification callback.
        """
        return ok
