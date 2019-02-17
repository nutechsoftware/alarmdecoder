"""
Message representations received from the panel through the `AlarmDecoder`_ (AD2)
devices.

:py:class:`LRRMessage`: Message received from a long-range radio module.

.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

from .. import BaseMessage
from ...util import InvalidMessageError

from .events import LRR_EVENT_TYPE, get_event_description, get_event_data_type, get_event_source


class LRRMessage(BaseMessage):
    """
    Represent a message from a Long Range Radio or emulated Long Range Radio.
    """
    event_data_type = None
    """Data Type for specific LRR message. User or Zone"""
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
    event_description = ''
    """Human-readable description of LRR event."""

    def __init__(self, data=None, skip_report_override=False):
        """
        Constructor

        :param data: message data to parse
        :type data: string
        """
        BaseMessage.__init__(self, data)

        self.skip_report_override = skip_report_override

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
            _, values = data.split(':')
            values = values.split(',')

            # Handle older-format events
            if len(values) <= 3:
                self.event_data, self.partition, self.event_type = values
                self.version = 1

            # Newer-format events
            else:
                self.event_data, self.partition, self.event_type, self.report_code = values
                self.version = 2

                event_type_data = self.event_type.split('_')
                self.event_prefix = event_type_data[0]                      # Ex: CID
                self.event_source = get_event_source(self.event_prefix)     # Ex: LRR_EVENT_TYPE.CID
                self.event_status = int(event_type_data[1][0])              # Ex: 1 or 3
                self.event_code = int(event_type_data[1][1:], 16)           # Ex: 0x100 = Medical

                # replace last 2 digits of event_code with report_code, if applicable.
                if not self.skip_report_override and self.report_code not in ['00', 'ff']:
                    self.event_code = int(event_type_data[1][1] + self.report_code, 16)
                self.event_description = get_event_description(self.event_source, self.event_code)
                self.event_data_type = get_event_data_type(self.event_source, self.event_code)

        except ValueError:
            raise InvalidMessageError('Received invalid message: {0}'.format(data))


    def dict(self, **kwargs):
        """
        Dictionary representation
        """
        return dict(
            time                  = self.timestamp,
            event_data            = self.event_data,
            event_data_type       = self.event_data_type,
            event_type            = self.event_type,
            partition             = self.partition,
            report_code           = self.report_code,
            event_prefix          = self.event_prefix,
            event_source          = self.event_source,
            event_status          = self.event_status,
            event_code            = hex(self.event_code),
            event_description     = self.event_description,
            **kwargs
        )
