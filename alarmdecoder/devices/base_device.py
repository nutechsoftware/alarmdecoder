"""
This module contains the base device type for the `AlarmDecoder`_ (AD2) family.

.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import threading

from ..util import CommError, TimeoutError, InvalidMessageError
from ..event import event

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
        self._buffer = b''
        self._device = None
        self._running = False
        self._read_thread = None

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

                except InvalidMessageError:
                    pass

                except SSL.WantReadError:
                    pass

                except CommError as err:
                    self._device.close()

                except Exception as err:
                    self._device.close()
                    self._running = False
                    raise