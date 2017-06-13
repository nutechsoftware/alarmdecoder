"""
Message representations received from the panel through the `AlarmDecoder`_ (AD2)
devices.

:py:class:`LRRMessage`: Message received from a long-range radio module.

.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

from .. import BaseMessage
from ...util import InvalidMessageError

from .events import LRR_EVENT_TYPE


class LRRMessage(BaseMessage):
    """
    Represent a message from a Long Range Radio or emulated Long Range Radio.
    """

    event_data = None
    """Data associated with the LRR message.  Usually user ID or zone."""
    partition = -1
    """The partition that this message applies to."""
    event_type = None
    """The type of the event that occurred."""
    version = 0
    """LRR message version"""

    report_code = 0xFF
    """The report code used to override the last two digits of the event type."""
    event_prefix = ''
    """Extracted prefix for the event_type."""
    event_source = LRR_EVENT_TYPE.UNKNOWN
    """Extracted event type source."""
    event_status = 0
    """Event status flag that represents triggered or restored events."""
    event_code = 0
    """Event code for the LRR message."""

    def __init__(self, data=None):
        """
        Constructor

        :param data: message data to parse
        :type data: string
        """
        BaseMessage.__init__(self)

        if data is not None:
            self._parse_message(data)

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
            values = values.split(',')
            if len(values) <= 3:
                self.event_data, self.partition, self.event_type = values
                self.version = 1
            else:
                self.event_data, self.partition, self.event_type, self.report_code = values
                self.version = 2

                event_type_data = self.event_type.split('_')
                self.event_prefix = event_type_data[0]
                self.event_source = _get_event_source(self.event_prefix)
                self.event_status = int(event_type_data[1][0])
                self.event_code = int(event_type_data[1][1:], 16)

        except ValueError:
            raise InvalidMessageError('Received invalid message: {0}'.format(data))


    def dict(self, **kwargs):
        """
        Dictionary representation.
        """
        return dict(
            time                  = self.timestamp,
            event_data            = self.event_data,
            event_type            = self.event_type,
            partition             = self.partition,
            report_code           = self.report_code,
            event_prefix          = self.event_prefix,
            event_source          = self.event_source,
            event_status          = self.event_status,
            event_code            = hex(self.event_code),
            **kwargs
        )


def _get_event_source(prefix):
    source = LRR_EVENT_TYPE.UNKNOWN

    if prefix == 'CID':
        source = LRR_EVENT_TYPE.CID
    elif prefix == 'DSC':
        source = LRR_EVENT_TYPE.DSC
    elif prefix == 'AD2':
        source = LRR_EVENT_TYPE.ALARMDECODER
    elif prefix == 'ADEMCO':
        source = LRR_EVENT_TYPE.ADEMCO

    return source
