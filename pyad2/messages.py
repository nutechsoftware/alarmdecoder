"""
Message representations received from the panel through the AD2 devices.

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import re

from .util import InvalidMessageError

class BaseMessage(object):
    """
    Base class for messages.
    """
    def __init__(self):
        """
        Constructor
        """
        self.raw = None

    def __str__(self):
        """
        String conversion operator.
        """
        return self.raw

class Message(BaseMessage):
    """
    Represents a message from the alarm panel.
    """

    def __init__(self, data=None):
        """
        Constructor

        :param data: Message data to parse.
        :type data: str
        """
        self.ready = False
        self.armed_away = False
        self.armed_home = False
        self.backlight_on = False
        self.programming_mode = False
        self.beeps = -1
        self.zone_bypassed = False
        self.ac_power = False
        self.chime_on = False
        self.alarm_event_occurred = False
        self.alarm_sounding = False
        self.battery_low = False
        self.entry_delay_off = False
        self.fire_alarm = False
        self.check_zone = False
        self.perimeter_only = False
        self.numeric_code = ""
        self.text = ""
        self.cursor_location = -1
        self.data = ""
        self.mask = ""
        self.bitfield = ""
        self.panel_data = ""

        self._regex = re.compile('("(?:[^"]|"")*"|[^,]*),("(?:[^"]|"")*"|[^,]*),("(?:[^"]|"")*"|[^,]*),("(?:[^"]|"")*"|[^,]*)')

        if data is not None:
            self._parse_message(data)

    def _parse_message(self, data):
        """
        Parse the message from the device.

        :param data: The message data.
        :type data: str

        :raises: InvalidMessageError
        """
        m = self._regex.match(data)

        if m is None:
            raise InvalidMessageError('Received invalid message: {0}'.format(data))

        self.bitfield, self.numeric_code, self.panel_data, alpha = m.group(1, 2, 3, 4)
        self.mask = int(self.panel_data[3:3+8], 16)

        is_bit_set = lambda bit: not self.bitfield[bit] == "0"

        self.raw = data
        self.ready = is_bit_set(1)
        self.armed_away = is_bit_set(2)
        self.armed_home = is_bit_set(3)
        self.backlight_on = is_bit_set(4)
        self.programming_mode = is_bit_set(5)
        self.beeps = int(self.bitfield[6], 16)
        self.zone_bypassed = is_bit_set(7)
        self.ac_power = is_bit_set(8)
        self.chime_on = is_bit_set(9)
        self.alarm_event_occurred = is_bit_set(10)
        self.alarm_sounding = is_bit_set(11)
        self.battery_low = is_bit_set(12)
        self.entry_delay_off = is_bit_set(13)
        self.fire_alarm = is_bit_set(14)
        self.check_zone = is_bit_set(15)
        self.perimeter_only = is_bit_set(16)
        # bits 17-20 unused.
        self.text = alpha.strip('"')

        if int(self.panel_data[19:21], 16) & 0x01 > 0:
            self.cursor_location = int(self.bitfield[21:23], 16)    # Alpha character index that the cursor is on.

    def __str__(self):
        """
        String conversion operator.
        """
        return self.raw

class ExpanderMessage(BaseMessage):
    """
    Represents a message from a zone or relay expansion module.
    """

    ZONE = 0
    """Flag indicating that the expander message relates to a Zone Expander."""
    RELAY = 1
    """Flag indicating that the expander message relates to a Relay Expander."""

    def __init__(self, data=None):
        """
        Constructor

        :param data: The message data to parse.
        :type data: str
        """
        self.type = None
        self.address = None
        self.channel = None
        self.value = None
        self.raw = None

        if data is not None:
            self._parse_message(data)

    def __str__(self):
        """
        String conversion operator.
        """
        return self.raw

    def _parse_message(self, data):
        """
        Parse the raw message from the device.

        :param data: The message data
        :type data: str
        """
        try:
            header, values = data.split(':')
            address, channel, value = values.split(',')

            self.raw = data
            self.address = int(address)
            self.channel = int(channel)
            self.value = int(value)

        except ValueError:
            raise InvalidMessageError('Received invalid message: {0}'.format(data))

        if header == '!EXP':
            self.type = ExpanderMessage.ZONE
        elif header == '!REL':
            self.type = ExpanderMessage.RELAY
        else:
            raise InvalidMessageError('Unknown expander message header: {0}'.format(data))

class RFMessage(BaseMessage):
    """
    Represents a message from an RF receiver.
    """

    def __init__(self, data=None):
        """
        Constructor

        :param data: The message data to parse
        :type data: str
        """
        self.raw = None
        self.serial_number = None
        self.value = None
        self.battery = None
        self.supervision = None
        self.loop = {}

        if data is not None:
            self._parse_message(data)

    def __str__(self):
        """
        String conversion operator.
        """
        return self.raw

    def _parse_message(self, data):
        """
        Parses the raw message from the device.

        :param data: The message data.
        :type data: str
        """
        try:
            self.raw = data

            _, values = data.split(':')
            self.serial_number, self.value = values.split(',')
            self.value = int(self.value, 16)

            is_bit_set = lambda b: self.value & (1 << b) > 0

            # Bit 1 = unknown
            self.battery = is_bit_set(2)
            self.supervision = is_bit_set(3)
            # Bit 8 = unknown
            self.loop[0] = is_bit_set(5)
            self.loop[1] = is_bit_set(6)
            self.loop[2] = is_bit_set(7)
            self.loop[3] = is_bit_set(8)

        except ValueError:
            raise InvalidMessageError('Received invalid message: {0}'.format(data))


class LRRMessage(BaseMessage):
    """
    Represent a message from a Long Range Radio.
    """

    def __init__(self, data=None):
        """
        Constructor

        :param data: The message data to parse.
        :type data: str
        """
        self.raw = None
        self.event_data = None
        self.partition = None
        self.event_type = None

        if data is not None:
            self._parse_message(data)

    def __str__(self):
        """
        String conversion operator.
        """
        return self.raw

    def _parse_message(self, data):
        """
        Parses the raw message from the device.

        :param data: The message data.
        :type data: str
        """
        try:
            self.raw = data

            _, values = data.split(':')
            self.event_data, self.partition, self.event_type = values.split(',')

        except ValueError:
            raise InvalidMessageError('Received invalid message: {0}'.format(data))
