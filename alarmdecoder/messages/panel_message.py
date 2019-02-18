"""
Message representations received from the panel through the `AlarmDecoder`_ (AD2)
devices.

:py:class:`Message`: The standard and most common message received from a panel.

.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import re

from . import BaseMessage
from ..util import InvalidMessageError
from ..panels import PANEL_TYPES, ADEMCO, DSC

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
    system_fault = -1
    """Indicates if any panel specific system fault exists."""
    panel_type = ADEMCO
    """Indicates which panel type was the source of this message."""
    numeric_code = None
    """The numeric code associated with the message."""
    text = None
    """The human-readable text to be displayed on the panel LCD."""
    cursor_location = -1
    """Current cursor location on the keypad."""
    mask = 0xFFFFFFFF
    """Address mask this message is intended for."""
    bitfield = None
    """The bitfield associated with this message."""
    panel_data = None
    """The panel data field associated with this message."""


    _regex = re.compile('^(!KPM:){0,1}(\[[a-fA-F0-9\-]+\]),([a-fA-F0-9]+),(\[[a-fA-F0-9]+\]),(".+")$')

    def __init__(self, data=None):
        """
        Constructor

        :param data: message data to parse
        :type data: string
        """
        BaseMessage.__init__(self, data)

        if data is not None:
            self._parse_message(data)

    def _parse_message(self, data):
        """
        Parse the message from the device.

        :param data: message data
        :type data: string

        :raises: :py:class:`~alarmdecoder.util.InvalidMessageError`
        """
        match = self._regex.match(str(data))

        if match is None:
            raise InvalidMessageError('Received invalid message: {0}'.format(data))

        header, self.bitfield, self.numeric_code, self.panel_data, alpha = match.group(1, 2, 3, 4, 5)

        is_bit_set = lambda bit: not self.bitfield[bit] == "0"

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
        self.system_fault = int(self.bitfield[17], 16)
        if self.bitfield[18] in list(PANEL_TYPES):
            self.panel_type = PANEL_TYPES[self.bitfield[18]]
        # pos 20-21 - Unused.
        self.text = alpha.strip('"')
        self.mask = int(self.panel_data[3:3+8], 16)

        if self.panel_type in (ADEMCO, DSC):
            if int(self.panel_data[19:21], 16) & 0x01 > 0:
                # Current cursor location on the alpha display.
                self.cursor_location = int(self.panel_data[21:23], 16)

    def parse_numeric_code(self, force_hex=False):
        """
        Parses and returns the numeric code as an integer.

        The numeric code can be either base 10 or base 16, depending on
        where the message came from.

        :param force_hex: force the numeric code to be processed as base 16.
        :type force_hex: boolean

        :raises: ValueError
        """
        code = None
        got_error = False

        if not force_hex:
            try:
                code = int(self.numeric_code)
            except ValueError:
                got_error = True

        if force_hex or got_error:
            try:
                code = int(self.numeric_code, 16)
            except ValueError:
                raise

        return code

    def dict(self, **kwargs):
        """
        Dictionary representation.
        """
        return dict(
            time                  = self.timestamp,
            bitfield              = self.bitfield,
            numeric_code          = self.numeric_code,
            panel_data            = self.panel_data,
            mask                  = self.mask,
            ready                 = self.ready,
            armed_away            = self.armed_away,
            armed_home            = self.armed_home,
            backlight_on          = self.backlight_on,
            programming_mode      = self.programming_mode,
            beeps                 = self.beeps,
            zone_bypassed         = self.zone_bypassed,
            ac_power              = self.ac_power,
            chime_on              = self.chime_on,
            alarm_event_occurred  = self.alarm_event_occurred,
            alarm_sounding        = self.alarm_sounding,
            battery_low           = self.battery_low,
            entry_delay_off       = self.entry_delay_off,
            fire_alarm            = self.fire_alarm,
            check_zone            = self.check_zone,
            perimeter_only        = self.perimeter_only,
            text                  = self.text,
            cursor_location       = self.cursor_location,
            **kwargs
        )
