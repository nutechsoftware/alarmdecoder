"""
Provides the full AD2USB class and factory.
"""

import time
import threading
import re
from .event import event
from . import devices
from . import util

class Overseer(object):
    """
    Factory for creation of AD2USB devices as well as provide4s attach/detach events."
    """

    # Factory events
    on_attached = event.Event('Called when an AD2USB device has been detected.')
    on_detached = event.Event('Called when an AD2USB device has been removed.')

    __devices = []

    @classmethod
    def find_all(cls):
        """
        Returns all AD2USB devices located on the system.
        """
        cls.__devices = devices.USBDevice.find_all()

        return cls.__devices

    @classmethod
    def devices(cls):
        """
        Returns a cached list of AD2USB devices located on the system.
        """
        return cls.__devices

    @classmethod
    def create(cls, device=None):
        """
        Factory method that returns the requested AD2USB device, or the first device.
        """
        cls.find_all()

        if len(cls.__devices) == 0:
            raise util.NoDeviceError('No AD2USB devices present.')

        if device is None:
            device = cls.__devices[0]

        vendor, product, sernum, ifcount, description = device
        device = devices.USBDevice(serial=sernum, description=description)

        return AD2USB(device)

    def __init__(self, attached_event=None, detached_event=None):
        """
        Constructor
        """
        self._detect_thread = Overseer.DetectThread(self)

        if attached_event:
            self.on_attached += attached_event

        if detached_event:
            self.on_detached += detached_event

        Overseer.find_all()

        self.start()

    def __del__(self):
        """
        Destructor
        """
        pass

    def close(self):
        """
        Clean up and shut down.
        """
        self.stop()

    def start(self):
        """
        Starts the detection thread, if not already running.
        """
        if not self._detect_thread.is_alive():
            self._detect_thread.start()

    def stop(self):
        """
        Stops the detection thread.
        """
        self._detect_thread.stop()

    def get_device(self, device=None):
        """
        Factory method that returns the requested AD2USB device, or the first device.
        """
        return Overseer.create(device)


    class DetectThread(threading.Thread):
        """
        Thread that handles detection of added/removed devices.
        """
        def __init__(self, overseer):
            """
            Constructor
            """
            threading.Thread.__init__(self)

            self._overseer = overseer
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
    """
    High-level wrapper around AD2USB/AD2SERIAL devices.
    """

    # High-level Events
    on_open = event.Event('Called when the device has been opened.')
    on_close = event.Event('Called when the device has been closed.')

    on_status_changed = event.Event('Called when the panel status changes.')
    on_power_changed = event.Event('Called when panel power switches between AC and DC.')
    on_alarm = event.Event('Called when the alarm is triggered.')
    on_bypass = event.Event('Called when a zone is bypassed.')

    # Mid-level Events
    on_message = event.Event('Called when a message has been received from the device.')

    # Low-level Events
    on_read = event.Event('Called when a line has been read from the device.')
    on_write = event.Event('Called when data has been written to the device.')

    def __init__(self, device):
        """
        Constructor
        """
        self._power_status = None
        self._alarm_status = None
        self._bypass_status = None
        self._device = device

    def __del__(self):
        """
        Destructor
        """
        pass

    def open(self, baudrate=None, interface=None, index=None):
        """
        Opens the device.
        """
        self._wire_events()
        self._device.open(baudrate=baudrate, interface=interface, index=index)

    def close(self):
        """
        Closes the device.
        """
        self._device.close()
        self._device = None

    def _wire_events(self):
        """
        Wires up the internal device events.
        """
        self._device.on_open += self._on_open
        self._device.on_close += self._on_close
        self._device.on_read += self._on_read
        self._device.on_write += self._on_write

    def _handle_message(self, data):
        """
        Parses messages from the panel.
        """
        if data[0] == '!':      # TEMP: Remove this.
            return None

        msg = Message(data)

        # parse and build stuff

        # TEMP
        address_mask = 0xFF80

        if address_mask & msg.mask > 0:
            #print 'ac={0}, alarm={1}, bypass={2}'.format(msg.ac, msg.alarm_bell, msg.bypass)
            if msg.ac != self._power_status:
                self._power_status, old_status = msg.ac, self._power_status
                #print '\tpower: new={0}, old={1}'.format(self._power_status, old_status)
                if old_status is not None:
                    self.on_power_changed(self._power_status)

            if msg.alarm_bell != self._alarm_status:
                self._alarm_status, old_status = msg.alarm_bell, self._alarm_status
                #print '\talarm: new={0}, old={1}'.format(self._alarm_status, old_status)
                if old_status is not None:
                    self.on_alarm(self._alarm_status)

            if msg.bypass != self._bypass_status:
                self._bypass_status, old_status = msg.bypass, self._bypass_status
                #print '\tbypass: new={0}, old={1}'.format(self._bypass_status, old_status)
                if old_status is not None:
                    self.on_bypass(self._bypass_status)

    def _on_open(self, sender, args):
        """
        Internal handler for opening the device.
        """
        self.on_open(args)

    def _on_close(self, sender, args):
        """
        Internal handler for closing the device.
        """
        self.on_close(args)

    def _on_read(self, sender, args):
        """
        Internal handler for reading from the device.
        """
        msg = self._handle_message(args)
        if msg:
            self.on_message(msg)

        self.on_read(args)

    def _on_write(self, sender, args):
        """
        Internal handler for writing to the device.
        """
        self.on_write(args)

class Message(object):
    """
    Represents a message from the alarm panel.
    """

    def __init__(self, data=None):
        """
        Constructor
        """
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
        self._raw = ""
        self._mask = ""

        self._msg_bitfields = ""
        self._msg_zone = ""
        self._msg_binary = ""
        self._msg_alpha = ""

        self._regex = re.compile('("(?:[^"]|"")*"|[^,]*),("(?:[^"]|"")*"|[^,]*),("(?:[^"]|"")*"|[^,]*),("(?:[^"]|"")*"|[^,]*)')

        if data is not None:
            self._parse_message(data)

    def _parse_message(self, data):
        m = self._regex.match(data)

        if m is None:
            raise util.InvalidMessageError('Received invalid message: {0}'.format(data))

        self._msg_bitfields, self._msg_zone, self._msg_binary, self._msg_alpha = m.group(1, 2, 3, 4)
        self.mask = int(self._msg_binary[3:3+8], 16)

        self.raw = data
        self.ready = not self._msg_bitfields[1:2] == "0"
        self.armed_away = not self._msg_bitfields[2:3] == "0"
        self.armed_home = not self._msg_bitfields[3:4] == "0"
        self.backlight = not self._msg_bitfields[4:5] == "0"
        self.programming_mode = not self._msg_bitfields[5:6] == "0"
        self.beeps = int(self._msg_bitfields[6:7], 16)
        self.bypass = not self._msg_bitfields[7:8] == "0"
        self.ac = not self._msg_bitfields[8:9] == "0"
        self.chime_mode = not self._msg_bitfields[9:10] == "0"
        self.alarm_event_occurred = not self._msg_bitfields[10:11] == "0"
        self.alarm_bell = not self._msg_bitfields[11:12] == "0"
        self.numeric = self._msg_zone
        self.text = self._msg_alpha.strip('"')

        if int(self._msg_binary[19:21], 16) & 0x01 > 0:
            self.cursor = int(self._msg_bitfields[21:23], 16)

        #print "Message:\r\n" \
        #        "\tmask: {0}\r\n" \
        #        "\tready: {1}\r\n" \
        #        "\tarmed_away: {2}\r\n" \
        #        "\tarmed_home: {3}\r\n" \
        #        "\tbacklight: {4}\r\n" \
        #        "\tprogramming_mode: {5}\r\n" \
        #        "\tbeeps: {6}\r\n" \
        #        "\tbypass: {7}\r\n" \
        #        "\tac: {8}\r\n" \
        #        "\tchime_mode: {9}\r\n" \
        #        "\talarm_event_occurred: {10}\r\n" \
        #        "\talarm_bell: {11}\r\n" \
        #        "\tcursor: {12}\r\n" \
        #        "\tnumeric: {13}\r\n" \
        #        "\ttext: {14}\r\n".format(
        #            self.mask,
        #            self.ready,
        #            self.armed_away,
        #            self.armed_home,
        #            self.backlight,
        #            self.programming_mode,
        #            self.beeps,
        #            self.bypass,
        #            self.ac,
        #            self.chime_mode,
        #            self.alarm_event_occurred,
        #            self.alarm_bell,
        #            self.cursor,
        #            self.numeric,
        #            self.text
        #        )

    @property
    def ignore_packet(self):
        """
        Indicates whether or not this message should be ignored.
        """
        return self._ignore_packet

    @ignore_packet.setter
    def ignore_packet(self, value):
        """
        Sets the value indicating whether or not this packet should be ignored.
        """
        self._ignore_packet = value

    @property
    def ready(self):
        """
        Indicates whether or not the panel is ready.
        """
        return self._ready

    @ready.setter
    def ready(self, value):
        """
        Sets the value indicating whether or not the panel is ready.
        """
        self._ready = value

    @property
    def armed_away(self):
        """
        Indicates whether or not the panel is armed in away mode.
        """
        return self._armed_away

    @armed_away.setter
    def armed_away(self, value):
        """
        Sets the value indicating whether or not the panel is armed in away mode.
        """
        self._armed_away = value

    @property
    def armed_home(self):
        """
        Indicates whether or not the panel is armed in home/stay mode.
        """
        return self._armed_home

    @armed_home.setter
    def armed_home(self, value):
        """
        Sets the value indicating whether or not the panel is armed in home/stay mode.
        """
        self._armed_home = value

    @property
    def backlight(self):
        """
        Indicates whether or not the panel backlight is on.
        """
        return self._backlight

    @backlight.setter
    def backlight(self, value):
        """
        Sets the value indicating whether or not the panel backlight is on.
        """
        self._backlight = value

    @property
    def programming_mode(self):
        """
        Indicates whether or not the panel is in programming mode.
        """
        return self._programming_mode

    @programming_mode.setter
    def programming_mode(self, value):
        """
        Sets the value indicating whether or not the panel is in programming mode.
        """
        self._programming_mode = value

    @property
    def beeps(self):
        """
        Returns the number of beeps associated with this message.
        """
        return self._beeps

    @beeps.setter
    def beeps(self, value):
        """
        Sets the number of beeps associated with this message.
        """
        self._beeps = value

    @property
    def bypass(self):
        """
        Indicates whether or not zones have been bypassed.
        """
        return self._bypass

    @bypass.setter
    def bypass(self, value):
        """
        Sets the value indicating whether or not zones have been bypassed.
        """
        self._bypass = value

    @property
    def ac(self):
        """
        Indicates whether or not the system is on AC power.
        """
        return self._ac

    @ac.setter
    def ac(self, value):
        """
        Sets the value indicating whether or not the system is on AC power.
        """
        self._ac = value

    @property
    def chime_mode(self):
        """
        Indicates whether or not panel chimes are enabled.
        """
        return self._chime_mode

    @chime_mode.setter
    def chime_mode(self, value):
        """
        Sets the value indicating whether or not the panel chimes are enabled.
        """
        self._chime_mode = value

    @property
    def alarm_event_occurred(self):
        """
        Indicates whether or not an alarm event has occurred.
        """
        return self._alarm_event_occurred

    @alarm_event_occurred.setter
    def alarm_event_occurred(self, value):
        """
        Sets the value indicating whether or not an alarm event has occurred.
        """
        self._alarm_event_occurred = value

    @property
    def alarm_bell(self):
        """
        Indicates whether or not an alarm is currently sounding.
        """
        return self._alarm_bell

    @alarm_bell.setter
    def alarm_bell(self, value):
        """
        Sets the value indicating whether or not an alarm is currently sounding.
        """
        self._alarm_bell = value

    @property
    def numeric(self):
        """
        Numeric indicator of associated with message.  For example: If zone #3 is faulted, this value is 003.
        """
        return self._numeric

    @numeric.setter
    def numeric(self, value):
        """
        Sets the numeric indicator associated with this message.
        """
        self._numeric = value

    @property
    def text(self):
        """
        Alphanumeric text associated with this message.
        """
        return self._text

    @text.setter
    def text(self, value):
        """
        Sets the alphanumeric text associated with this message.
        """
        self._text = value

    @property
    def cursor(self):
        """
        Indicates which text position has the cursor underneath it.
        """
        return self._cursor

    @cursor.setter
    def cursor(self, value):
        """
        Sets the value indicating which text position has the cursor underneath it.
        """
        self._cursor = value

    @property
    def raw(self):
        """
        Raw representation of the message data from the panel.
        """
        return self._raw

    @raw.setter
    def raw(self, value):
        """
        Sets the raw representation of the message data from the panel.
        """
        self._raw = value

    @property
    def mask(self):
        """
        The panel mask for which this message is intended.
        """
        return self._mask

    @mask.setter
    def mask(self, value):
        """
        Sets the panel mask for which this message is intended.
        """
        self._mask = value
