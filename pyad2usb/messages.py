"""
Message representations received from the panel through the AD2USB.
"""

import re

class Message(object):
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

        :raises: util.InvalidMessageError
        """
        m = self._regex.match(data)

        if m is None:
            raise util.InvalidMessageError('Received invalid message: {0}'.format(data))

        self.bitfield, self.numeric_code, self.panel_data, alpha = m.group(1, 2, 3, 4)
        self.mask = int(self.panel_data[3:3+8], 16)

        self.raw = data
        self.ready = not self.bitfield[1:2] == "0"
        self.armed_away = not self.bitfield[2:3] == "0"
        self.armed_home = not self.bitfield[3:4] == "0"
        self.backlight_on = not self.bitfield[4:5] == "0"
        self.programming_mode = not self.bitfield[5:6] == "0"
        self.beeps = int(self.bitfield[6:7], 16)
        self.zone_bypassed = not self.bitfield[7:8] == "0"
        self.ac_power = not self.bitfield[8:9] == "0"
        self.chime_on = not self.bitfield[9:10] == "0"
        self.alarm_event_occurred = not self.bitfield[10:11] == "0"
        self.alarm_sounding = not self.bitfield[11:12] == "0"
        self.battery_low = not self.bitfield[12:13] == "0"
        self.entry_delay_off = not self.bitfield[13:14] == "0"
        self.fire_alarm = not self.bitfield[14:15] == "0"
        self.check_zone = not self.bitfield[15:16] == "0"
        self.perimeter_only = not self.bitfield[16:17] == "0"
        # bits 17-20 unused.
        self.text = alpha.strip('"')

        if int(self.panel_data[19:21], 16) & 0x01 > 0:
            self.cursor_location = int(self.bitfield[21:23], 16)    # Alpha character index that the cursor is on.

    def __str__(self):
        """
        String conversion operator.
        """
        return 'msg > {0:0<9} [{1}{2}{3}] -- ({4}) {5}'.format(hex(self.mask), 1 if self.ready else 0, 1 if self.armed_away else 0, 1 if self.armed_home else 0, self.numeric_code, self.text)

class ExpanderMessage(object):
    """
    Represents a message from a zone or relay expansion module.
    """

    ZONE = 0
    RELAY = 1

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
        expander_type = 'UNKWN'
        if self.type == ExpanderMessage.ZONE:
            expander_type = 'ZONE'
        elif self.type  == ExpanderMessage.RELAY:
            expander_type = 'RELAY'

        return 'exp > [{0: <5}] {1}/{2} -- {3}'.format(expander_type, self.address, self.channel, self.value)

    def _parse_message(self, data):
        """
        Parse the raw message from the device.

        :param data: The message data
        :type data: str
        """
        header, values = data.split(':')
        address, channel, value = values.split(',')

        self.raw = data
        self.address = int(address)
        self.channel = int(channel)
        self.value = int(value)

        if header == '!EXP':
            self.type = ExpanderMessage.ZONE
        elif header == '!REL':
            self.type = ExpanderMessage.RELAY

class RFMessage(object):
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
        self.loop = dict()

        if data is not None:
            self._parse_message(data)

    def __str__(self):
        """
        String conversion operator.
        """
        return 'rf > {0}: {1:x}'.format(self.serial_number, self.value)

    def _parse_message(self, data):
        """
        Parses the raw message from the device.

        :param data: The message data.
        :type data: str
        """
        self.raw = data

        _, values = data.split(':')
        self.serial_number, self.value = values.split(',')
        self.value = int(self.value, 16)

        test_bit = lambda v, b: v & (1 << b) > 0

        # Bit 1 = unknown
        self.battery = test_bit(self.value, 2)
        self.supervision = test_bit(self.value, 3)
        # Bit 8 = unknown
        self.loop[0] = test_bit(self.value, 5)
        self.loop[1] = test_bit(self.value, 6)
        self.loop[2] = test_bit(self.value, 7)
        self.loop[3] = test_bit(self.value, 8)

class LRRMessage(object):
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
        self._event_data = None
        self._partition = None
        self._event_type = None

        if data is not None:
            self._parse_message(data)

    def __str__(self):
        """
        String conversion operator.
        """
        return 'lrr > {0} @ {1} -- {2}'.format()

    def _parse_message(self, data):
        """
        Parses the raw message from the device.

        :param data: The message data.
        :type data: str
        """
        self.raw = data

        _, values = data.split(':')
        self._event_data, self._partition, self._event_type = values.split(',')
