from pyftdi.pyftdi.ftdi import *
from pyftdi.pyftdi.usbtools import *
import time
import usb.core
import usb.util

class AD2USB(object):
	@classmethod
	def find_all(cls):
		cls.__devices = Device.find_all()

		return cls.__devices

	def __init__(self):
		self._device = None

		AD2USB.find_all()

	def __del__(self):
		pass

	def open(self, device=None):
		if len(cls.__devices) == 0:
			raise NoDeviceError

		if device is None:
			self._device = cls.__devices[0]
		else
			self._device = device

		self._device.open()

	def close(self):
		self._device.close()
		self._device = None



class Device(object):
    FTDI_VENDOR_ID = 0x0403
    FTDI_PRODUCT_ID = 0x6001
    BAUDRATE = 115200

    @staticmethod
    def find_all():
        devices = []

        try:
            devices = Ftdi.find_all([(FTDI_VENDOR_ID, FTDI_PRODUCT_ID)], nocache=True)
        except usb.core.USBError, e:
            pass

        return devices

    def __init__(self, vid=FTDI_VENDOR_ID, pid=FTDI_PRODUCT_ID, serial=None, description=None):
        self._vendor_id = vid
        self._product_id = pid
        self._serial_number = serial
        self._description = description
        self._buffer = ''
        self._device = Ftdi()

    def open(self, baudrate=BAUDRATE, interface=0, index=0):
        self._device.open(self._vendor_id,
                         self._product_id,
                         interface,
                         index,
                         self._serial_number,
                         self._description)

        self.device.set_baudrate(baudrate)

    def close(self):
        try:
            self._device.close()
        except FtdiError, e:
            pass

    def write(self, data):
        self._device.write_data(data)

    def read_line(self, timeout=0.0):
        start_time = time.time()
        got_line = False
        ret = None

        try:
            while 1:
                buf = self._device.read_data(1)
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
                    break

                time.sleep(0.01)
        except FtdiError, e:
            pass
        else:
            if got_line:
                ret = self._buffer
                self._buffer = ''

        return ret
