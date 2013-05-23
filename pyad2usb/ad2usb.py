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


        self._address_mask = 0xFF80     # TEMP

    def __del__(self):
        """
        Destructor
        """
        pass

    def open(self, baudrate=None, interface=None, index=None, no_read_thread=False):
        """
        Opens the device.
        """
        self._wire_events()
        self._device.open(baudrate=baudrate, interface=interface, index=index, no_read_thread=no_read_thread)

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
        msg = None

        if data[0] != '!':
            msg = Message(data)

            if self._address_mask & msg.mask > 0:
                self._update_internal_states(msg)

        else:   # specialty messages
            header = data[0:4]

            if header == '!EXP' or header == '!REL':
                msg = ExpanderMessage(data)
            elif header == '!RFX':
                msg = RFMessage(data)

        return msg

    def _update_internal_states(self, message):
        if message.ac_power != self._power_status:
            self._power_status, old_status = message.ac_power, self._power_status

            if old_status is not None:
                self.on_power_changed(self._power_status)

        if message.alarm_sounding != self._alarm_status:
            self._alarm_status, old_status = message.alarm_sounding, self._alarm_status

            if old_status is not None:
                self.on_alarm(self._alarm_status)

        if message.zone_bypassed != self._bypass_status:
            self._bypass_status, old_status = message.zone_bypassed, self._bypass_status

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
        self.on_read(args)

        msg = self._handle_message(args)
        if msg:
            self.on_message(msg)

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
        self._ready = False
        self._armed_away = False
        self._armed_home = False
        self._backlight_on = False
        self._programming_mode = False
        self._beeps = -1
        self._zone_bypassed = False
        self._ac_power = False
        self._chime_on = False
        self._alarm_event_occurred = False
        self._alarm_sounding = False
        self._numeric_code = ""
        self._text = ""
        self._cursor_location = -1
        self._data = ""
        self._mask = ""
        self._bitfield = ""
        self._panel_data = ""

        self._regex = re.compile('("(?:[^"]|"")*"|[^,]*),("(?:[^"]|"")*"|[^,]*),("(?:[^"]|"")*"|[^,]*),("(?:[^"]|"")*"|[^,]*)')

        if data is not None:
            self._parse_message(data)

    def _parse_message(self, data):
        """
        Parse the message from the device.
        """
        m = self._regex.match(data)

        if m is None:
            raise util.InvalidMessageError('Received invalid message: {0}'.format(data))

        self._bitfield, self._numeric_code, self._panel_data, alpha = m.group(1, 2, 3, 4)
        self._mask = int(self._panel_data[3:3+8], 16)

        self._data = data
        self._ready = not self._bitfield[1:2] == "0"
        self._armed_away = not self._bitfield[2:3] == "0"
        self._armed_home = not self._bitfield[3:4] == "0"
        self._backlight_on = not self._bitfield[4:5] == "0"
        self._programming_mode = not self._bitfield[5:6] == "0"
        self._beeps = int(self._bitfield[6:7], 16)
        self._zone_bypassed = not self._bitfield[7:8] == "0"
        self._ac_power = not self._bitfield[8:9] == "0"
        self._chime_on = not self._bitfield[9:10] == "0"
        self._alarm_event_occurred = not self._bitfield[10:11] == "0"
        self._alarm_sounding = not self._bitfield[11:12] == "0"
        self._text = alpha.strip('"')

        if int(self._panel_data[19:21], 16) & 0x01 > 0:
            self._cursor_location = int(self._bitfield[21:23], 16)    # Alpha character index that the cursor is on.

    def __str__(self):
        """
        String conversion operator.
        """
        return 'msg > {0:0<9} [{1}{2}{3}] -- ({4}) {5}'.format(hex(self.mask), 1 if self.ready else 0, 1 if self.armed_away else 0, 1 if self.armed_home else 0, self.numeric_code, self.text)

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
    def backlight_on(self):
        """
        Indicates whether or not the panel backlight is on.
        """
        return self._backlight_on

    @backlight_on.setter
    def backlight_on(self, value):
        """
        Sets the value indicating whether or not the panel backlight is on.
        """
        self._backlight_on = value

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
    def zone_bypassed(self):
        """
        Indicates whether or not zones have been bypassed.
        """
        return self._zone_bypassed

    @zone_bypassed.setter
    def zone_bypassed(self, value):
        """
        Sets the value indicating whether or not zones have been bypassed.
        """
        self._zone_bypassed = value

    @property
    def ac_power(self):
        """
        Indicates whether or not the system is on AC power.
        """
        return self._ac_power

    @ac_power.setter
    def ac_power(self, value):
        """
        Sets the value indicating whether or not the system is on AC power.
        """
        self._ac_power = value

    @property
    def chime_on(self):
        """
        Indicates whether or not panel chimes are enabled.
        """
        return self._chime_on

    @chime_on.setter
    def chime_on(self, value):
        """
        Sets the value indicating whether or not the panel chimes are enabled.
        """
        self._chime_on = value

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
    def alarm_sounding(self):
        """
        Indicates whether or not an alarm is currently sounding.
        """
        return self._alarm_sounding

    @alarm_sounding.setter
    def alarm_sounding(self, value):
        """
        Sets the value indicating whether or not an alarm is currently sounding.
        """
        self._alarm_sounding = value

    @property
    def numeric_code(self):
        """
        Numeric indicator of associated with message.  For example: If zone #3 is faulted, this value is 003.
        """
        return self._numeric_code

    @numeric_code.setter
    def numeric_code(self, value):
        """
        Sets the numeric indicator associated with this message.
        """
        self._numeric_code = value

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
    def cursor_location(self):
        """
        Indicates which text position has the cursor underneath it.
        """
        return self._cursor_location

    @cursor_location.setter
    def cursor_location(self, value):
        """
        Sets the value indicating which text position has the cursor underneath it.
        """
        self._cursor_location = value

    @property
    def data(self):
        """
        Raw representation of the message from the panel.
        """
        return self._data

    @data.setter
    def data(self, value):
        """
        Sets the raw representation of the message from the panel.
        """
        self._data = value

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

    @property
    def bitfield(self):
        """
        The bit field associated with this message.
        """
        return self._bitfield

    @bitfield.setter
    def bitfield(self, value):
        """
        Sets the bit field associated with this message.
        """
        self._bitfield = value

    @property
    def panel_data(self):
        """
        The binary field associated with this message.
        """
        return self._panel_data

    @panel_data.setter
    def panel_data(self, value):
        """
        Sets the binary field associated with this message.
        """
        self._panel_data = value

class ExpanderMessage(object):
    """
    Represents a message from a zone or relay expansion module.
    """
    ZONE = 0
    RELAY = 1

    def __init__(self, data=None):
        """
        Constructor
        """
        self._type = None
        self._address = None
        self._channel = None
        self._value = None
        self._raw = None

        if data is not None:
            self._parse_message(data)

    def __str__(self):
        """
        String conversion operator.
        """
        expander_type = 'UNKWN'
        if self.type == ExpanderMessage.ZONE:
            expander_type = 'ZONE'
        elif self.type  == ExpanderMessage.RELAY:
            expander_type = 'RELAY'

        return 'exp > [{0: <5}] {1}/{2} -- {3}'.format(expander_type, self.address, self.channel, self.value)

    def _parse_message(self, data):
        """
        Parse the raw message from the device.
        """
        header, values = data.split(':')
        address, channel, value = values.split(',')

        self.raw = data
        self.address = address
        self.channel = channel
        self.value = value

        if header == '!EXP':
            self.type = ExpanderMessage.ZONE
        elif header == '!REL':
            self.type = ExpanderMessage.RELAY

    @property
    def address(self):
        """
        The relay address from which the message originated.
        """
        return self._address

    @address.setter
    def address(self, value):
        """
        Sets the relay address from which the message originated.
        """
        self._address = value

    @property
    def channel(self):
        """
        The zone expander channel from which the message originated.
        """
        return self._channel

    @channel.setter
    def channel(self, value):
        """
        Sets the zone expander channel from which the message originated.
        """
        self._channel = value

    @property
    def value(self):
        """
        The value associated with the message.
        """
        return self._value

    @value.setter
    def value(self, value):
        """
        Sets the value associated with the message.
        """
        self._value = value

    @property
    def raw(self):
        """
        The raw message from the expander device.
        """
        return self._raw

    @raw.setter
    def raw(self, value):
        """
        Sets the raw message from the expander device.
        """
        self._value = value

    @property
    def type(self):
        """
        The type of expander associated with this message.
        """
        return self._type

    @type.setter
    def type(self, value):
        """
        Sets the type of expander associated with this message.
        """
        self._type = value

class RFMessage(object):
    """
    Represents a message from an RF receiver.
    """
    def __init__(self, data=None):
        """
        Constructor
        """
        self._raw = None
        self._serial_number = None
        self._value = None

        if data is not None:
            self._parse_message(data)

    def __str__(self):
        """
        String conversion operator.
        """
        return 'rf > {0}: {1}'.format(self.serial_number, self.value)

    def _parse_message(self, data):
        """
        Parses the raw message from the device.
        """
        self.raw = data

        _, values = data.split(':')
        self.serial_number, self.value = values.split(',')

    @property
    def serial_number(self):
        """
        The serial number for the RF receiver.
        """
        return self._serial_number

    @serial_number.setter
    def serial_number(self, value):
        self._serial_number = value

    @property
    def value(self):
        """
        The value of the RF message.
        """
        return self._value

    @value.setter
    def value(self, value):
        """
        Sets the value of the RF message.
        """
        self._value = value

    @property
    def raw(self):
        """
        The raw message from the RF receiver.
        """
        return self._raw

    @raw.setter
    def raw(self, value):
        """
        Sets the raw message from the RF receiver.
        """
        self._raw = value
