"""
Message representations received from the panel through the `AlarmDecoder`_ (AD2)
devices.

:py:class:`RFMessage`: Message received from an RF receiver module.

.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

from . import BaseMessage
from ..util import InvalidMessageError

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
    loop = [False for _ in list(range(4))]
    """Loop indicators"""

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
        Parses the raw message from the device.

        :param data: message data
        :type data: string

        :raises: :py:class:`~alarmdecoder.util.InvalidMessageError`
        """
        try:
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

    def dict(self, **kwargs):
        """
        Dictionary representation.
        """
        return dict(
            time                  = self.timestamp,
            serial_number         = self.serial_number,
            value                 = self.value,
            battery               = self.battery,
            supervision           = self.supervision,
            **kwargs
        )
