import time
import threading
from .event import event
from . import devices
from . import util

class Overseer(object):
    on_attached = event.Event('Called when an AD2USB device has been detected.')
    on_detached = event.Event('Called when an AD2USB device has been removed.')

    __devices = []

    @classmethod
    def find_all(cls):
        cls.__devices = devices.USBDevice.find_all()

        return cls.__devices

    @classmethod
    def devices(cls):
        return cls.__devices

    @classmethod
    def create(cls, device=None):
        if len(cls.__devices) == 0:
            raise util.NoDeviceError('No AD2USB devices present.')

        if device is None:
            device = cls.__devices[0]

        vendor, product, sernum, ifcount, description = device
        device = devices.USBDevice(serial=sernum, description=description)

        return AD2USB(device)

    def __init__(self, attached_event=None, detached_event=None):
        self._detect_thread = Overseer.DetectThread(self)

        if attached_event:
            self.on_attached += attached_event

        if detached_event:
            self.on_detached += detached_event

        Overseer.find_all()

        self.start()

    def __del__(self):
        pass

    def close(self):
        self.stop()

    def start(self):
        self._detect_thread.start()

    def stop(self):
        self._detect_thread.stop()

    def get_device(self, device=None):
        return Overseer.create(device)


    class DetectThread(threading.Thread):
        def __init__(self, overseer):
            threading.Thread.__init__(self)

            self._overseer = overseer
            self._running = False

        def stop(self):
            self._running = False

        def run(self):
            self._running = True

            last_devices = set()

            while self._running:
                try:
                    Overseer.find_all()

                    current_devices = set(Overseer.devices())
                    new_devices = [d for d in current_devices if d not in last_devices]
                    removed_devices = [d for d in last_devices if d not in current_devices]
                    last_devices = current_devices

                    for d in new_devices:
                        self._overseer.on_attached(d)

                    for d in removed_devices:
                        self._overseer.on_detached(d)
                except util.CommError, err:
                    pass

                time.sleep(0.25)


class AD2USB(object):
    on_open = event.Event('Called when the device has been opened')
    on_close = event.Event('Called when the device has been closed')
    on_read = event.Event('Called when a line has been read from the device')
    on_write = event.Event('Called when data has been written to the device')

    def __init__(self, device):
        self._device = device

    def __del__(self):
        pass

    def open(self, baudrate=None, interface=None, index=None):
        self._wire_events()
        self._device.open(baudrate=baudrate, interface=interface, index=index)

    def close(self):
        self._device.close()
        self._device = None

    def _wire_events(self):
        self._device.on_open += self._on_open
        self._device.on_close += self._on_close
        self._device.on_read += self._on_read
        self._device.on_write += self._on_write

    def _on_open(self, sender, args):
        print '_on_open: {0}'.format(args)

        self.on_open(args)

    def _on_close(self, sender, args):
        print '_on_close: {0}'.format(args)

        self.on_close(args)

    def _on_read(self, sender, args):
        print '_on_read: {0}'.format(args)

        self.on_read(args)

    def _on_write(self, sender, args):
        print '_on_write: {0}'.format(args)

        self.on_write(args)
