"""
Message representations received from the panel through the `AlarmDecoder`_ (AD2)
devices.

:py:class:`ExpanderMessage`: Messages received from Relay or Zone expander modules.

.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

from . import BaseMessage
from ..util import InvalidMessageError

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
        BaseMessage.__init__(self, data)

        if data is not None:
            self._parse_message(data)

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

    def dict(self, **kwargs):
        """
        Dictionary representation.
        """
        return dict(
            time                  = self.timestamp,
            address               = self.address,
            channel               = self.channel,
            value                 = self.value,
            **kwargs
        )
