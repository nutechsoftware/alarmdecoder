"""
Message representations received from the panel through the `AlarmDecoder`_ (AD2)
devices.

:py:class:`AUIMessage`: Message received destined for an AUI keypad.

.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

from . import BaseMessage
from ..util import InvalidMessageError

class AUIMessage(BaseMessage):
    """
    Represents a message destined for an AUI keypad.
    """

    value = None
    """Raw value of the AUI message"""

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
        header, value = data.split(':')

        self.value = value

    def dict(self, **kwargs):
        """
        Dictionary representation.
        """
        return dict(
            value = self.value,
            **kwargs
        )