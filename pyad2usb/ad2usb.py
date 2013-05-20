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
        cls.find_all()

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
        if not self._detect_thread.is_alive():
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

    on_message = event.Event('Called when a message has been received from the device.')

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

    def _handle_message(self, data):
        if data[0] == '!':
            return None

        msg = Message()
        msg.ignore_packet = True

        print msg.ignore_packet

    def _on_open(self, sender, args):
        self.on_open(args)

    def _on_close(self, sender, args):
        self.on_close(args)

    def _on_read(self, sender, args):
        msg = self._handle_message(args)
        if msg:
            self.on_message(msg)

        self.on_read(args)

    def _on_write(self, sender, args):
        self.on_write(args)

class Message(object):
    def __init__(self):
        self._ignore_packet = False
        self._ready = False
        self._armed_away = False
        self._armed_home = False
        self._backlight = False
        self._programming_mode = False
        self._beeps = -1
        self._bypass = False
        self._ac = False
        self._chime_mode = False
        self._alarm_event_occurred = False
        self._alarm_bell = False
        self._numeric = ""
        self._text = ""
        self._cursor = -1
        self._raw_text = ""

    @property
    def ignore_packet(self):
        return self._ignore_packet

    @ignore_packet.setter
    def ignore_packet(self, value):
        self._ignore_packet = value

    @property
    def ready(self):
        return self._ready

    @ready.setter
    def ready(self, value):
        self._ready = value

    @property
    def armed_away(self):
        return self._armed_away

    @armed_away.setter
    def armed_away(self, value):
        self._armed_away = value

    @property
    def armed_home(self):
        return self._armed_home

    @armed_home.setter
    def armed_home(self, value):
        self._armed_home = value

    @property
    def backlight(self):
        return self._backlight

    @backlight.setter
    def backlight(self, value):
        self._backlight = value

    @property
    def programming_mode(self):
        return self._programming_mode

    @programming_mode.setter
    def programming_mode(self, value):
        self._programming_mode = value

    @property
    def beeps(self):
        return self._beeps

    @beeps.setter
    def beeps(self, value):
        self._beeps = value

    @property
    def bypass(self):
        return self._bypass

    @bypass.setter
    def bypass(self, value):
        self._bypass = value

    @property
    def ac(self):
        return self._ac

    @ac.setter
    def ac(self, value):
        self._ac = value

    @property
    def chime_mode(self):
        return self._chime_mode

    @chime_mode.setter
    def chime_mode(self, value):
        self._chime_mode = value

    @property
    def alarm_event_occurred(self):
        return self._alarm_event_occurred

    @alarm_event_occurred.setter
    def alarm_event_occurred(self, value):
        self._alarm_event_occurred = value

    @property
    def alarm_bell(self):
        return self._alarm_bell

    @alarm_bell.setter
    def alarm_bell(self, value):
        self._alarm_bell = value

    @property
    def numeric(self):
        return self._numeric

    @numeric.setter
    def numeric(self, value):
        self._numeric = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    @property
    def cursor(self):
        return self._cursor

    @cursor.setter
    def cursor(self, value):
        self._cursor = value

    @property
    def raw_text(self):
        return self._raw_text

    @raw_text.setter
    def raw_text(self, value):
        self._raw_text = value
