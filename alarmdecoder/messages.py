"""
Message representations received from the panel through the `AlarmDecoder`_ (AD2)
devices.

* :py:class:`Message`: The standard and most common message received from a panel.
* :py:class:`ExpanderMessage`: Messages received from Relay or Zone expander modules.
* :py:class:`RFMessage`: Message received from an RF receiver module.
* :py:class:`LRRMessage`: Message received from a long-range radio module.

.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import re

from .util import InvalidMessageError


class BaseMessage(object):
    """
    Base class for messages.
    """

    raw = None
    """The raw message text"""

    def __init__(self):
        """
        Constructor
        """
        pass

    def __str__(self):
        """
        String conversion operator.
        """
        return self.raw


class Message(BaseMessage):
    """
    Represents a message from the alarm panel.
    """

    ready = False
    """Indicates whether or not the panel is in a ready state."""
    armed_away = False
    """Indicates whether or not the panel is armed away."""
    armed_home = False
    """Indicates whether or not the panel is armed home."""
    backlight_on = False
    """Indicates whether or not the keypad backlight is on."""
    programming_mode = False
    """Indicates whether or not we're in programming mode."""
    beeps = -1
    """Number of beeps associated with a message."""
    zone_bypassed = False
    """Indicates whether or not a zone is bypassed."""
    ac_power = False
    """Indicates whether or not the panel is on AC power."""
    chime_on = False
    """Indicates whether or not the chime is enabled."""
    alarm_event_occurred = False
    """Indicates whether or not an alarm event has occurred."""
    alarm_sounding = False
    """Indicates whether or not an alarm is sounding."""
    battery_low = False
    """Indicates whether or not there is a low battery."""
    entry_delay_off = False
    """Indicates whether or not the entry delay is enabled."""
    fire_alarm = False
    """Indicates whether or not a fire alarm is sounding."""
    check_zone = False
    """Indicates whether or not there are zones that require attention."""
    perimeter_only = False
    """Indicates whether or not the perimeter is armed."""
    numeric_code = None
    """The numeric code associated with the message."""
    text = None
    """The human-readable text to be displayed on the panel LCD."""
    cursor_location = -1
    """Current cursor location on the keypad."""
    mask = None
    """Address mask this message is intended for."""
    bitfield = None
    """The bitfield associated with this message."""
    panel_data = None
    """The panel data field associated with this message."""

    def __init__(self, data=None):
        """
        Constructor

        :param data: message data to parse
        :type data: string
        """
        BaseMessage.__init__(self)

        self._regex = re.compile('^(!KPM:){0,1}(\[[a-fA-F0-9\-]+\]),([a-fA-F0-9]+),(\[[a-fA-F0-9]+\]),(".+")$')

        if data is not None:
            self._parse_message(data)

    def __str__(self):
        """
        String conversion operator.
        """
        return self.raw

    def _parse_message(self, data):
        """
        Parse the message from the device.

        :param data: message data
        :type data: string

        :raises: :py:class:`~alarmdecoder.util.InvalidMessageError`
        """
        match = self._regex.match(data)

        if match is None:
            raise InvalidMessageError('Received invalid message: {0}'.format(data))

        header, self.bitfield, self.numeric_code, self.panel_data, alpha = match.group(1, 2, 3, 4, 5)
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
            # Current cursor location on the alpha display.
            self.cursor_location = int(self.bitfield[21:23], 16)


class ExpanderMessage(BaseMessage):
    """
    Represents a message from a zone or relay expansion module.
    """

    ZONE = 0
    """Flag indicating that the expander message relates to a Zone Expander."""
    RELAY = 1
    """Flag indicating that the expander message relates to a Relay Expander."""

    type = None
    """Expander message type: ExpanderMessage.ZONE or ExpanderMessage.RELAY"""
    address = -1
    """Address of expander"""
    channel = -1
    """Channel on the expander"""
    value = -1
    """Value associated with the message"""

    def __init__(self, data=None):
        """
        Constructor

        :param data: message data to parse
        :type data: string
        """
        BaseMessage.__init__(self)

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

        :param data: message data
        :type data: string

        :raises: :py:class:`~alarmdecoder.util.InvalidMessageError`
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

    serial_number = None
    """Serial number of the RF device."""
    value = -1
    """Value associated with this message."""
    battery = False
    """Low battery indication"""
    supervision = False
    """Supervision required indication"""
    loop = [False for _ in range(4)]
    """Loop indicators"""

    def __init__(self, data=None):
        """
        Constructor

        :param data: message data to parse
        :type data: string
        """
        BaseMessage.__init__(self)

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

        :param data: message data
        :type data: string

        :raises: :py:class:`~alarmdecoder.util.InvalidMessageError`
        """
        try:
            self.raw = data

            _, values = data.split(':')
            self.serial_number, self.value = values.split(',')
            self.value = int(self.value, 16)

            is_bit_set = lambda b: self.value & (1 << (b - 1)) > 0

            # Bit 1 = unknown
            self.battery = is_bit_set(2)
            self.supervision = is_bit_set(3)
            # Bit 4 = unknown
            self.loop[2] = is_bit_set(5)
            self.loop[1] = is_bit_set(6)
            self.loop[3] = is_bit_set(7)
            self.loop[0] = is_bit_set(8)

        except ValueError:
            raise InvalidMessageError('Received invalid message: {0}'.format(data))


class LRRMessage(BaseMessage):
    """
    Represent a message from a Long Range Radio.
    """

    event_data = None
    """Data associated with the LRR message.  Usually user ID or zone."""
    partition = -1
    """The partition that this message applies to."""
    event_type = None
    """The type of the event that occurred."""

    def __init__(self, data=None):
        """
        Constructor

        :param data: message data to parse
        :type data: string
        """
        BaseMessage.__init__(self)

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

        :param data: message data to parse
        :type data: string

        :raises: :py:class:`~alarmdecoder.util.InvalidMessageError`
        """
        try:
            self.raw = data

            _, values = data.split(':')
            self.event_data, self.partition, self.event_type = values.split(',')

        except ValueError:
            raise InvalidMessageError('Received invalid message: {0}'.format(data))
