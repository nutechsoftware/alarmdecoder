"""
Primary system for handling LRR events.

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

from .events import LRR_EVENT_TYPE, LRR_EVENT_STATUS, LRR_CID_EVENT, LRR_DATA_TYPE
from .events import LRR_FIRE_EVENTS, LRR_POWER_EVENTS, LRR_BYPASS_EVENTS, LRR_BATTERY_EVENTS, \
                    LRR_PANIC_EVENTS, LRR_ARM_EVENTS, LRR_STAY_EVENTS, LRR_ALARM_EVENTS


class LRRSystem(object):
    """
    Handles LRR events and triggers higher-level events in the AlarmDecoder object.
    """

    def __init__(self, alarmdecoder_object):
        """
        Constructor

        :param alarmdecoder_object: Main AlarmDecoder object
        :type alarmdecoder_object: :py:class:`~alarmdecoder.AlarmDecoder`
        """
        self._alarmdecoder = alarmdecoder_object

    def update(self, message):
        """
        Updates the states in the primary AlarmDecoder object based on
        the LRR message provided.

        :param message: LRR message object
        :type message: :py:class:`~alarmdecoder.messages.LRRMessage`
        """
        # Firmware version < 2.2a.8.6
        if message.version == 1:
            if message.event_type == 'ALARM_PANIC':
                self._alarmdecoder._update_panic_status(True)
                
            elif message.event_type == 'CANCEL':
                self._alarmdecoder._update_panic_status(False)

        # Firmware version >= 2.2a.8.6
        elif message.version == 2:
            source = message.event_source
            if source == LRR_EVENT_TYPE.CID:
                self._handle_cid_message(message)
            elif source == LRR_EVENT_TYPE.DSC:
                self._handle_dsc_message(message)
            elif source == LRR_EVENT_TYPE.ADEMCO:
                self._handle_ademco_message(message)
            elif source == LRR_EVENT_TYPE.ALARMDECODER:
                self._handle_alarmdecoder_message(message)
            elif source == LRR_EVENT_TYPE.UNKNOWN:
                self._handle_unknown_message(message)
            else:
                pass

    def _handle_cid_message(self, message):
        """
        Handles ContactID LRR events.

        :param message: LRR message object
        :type message: :py:class:`~alarmdecoder.messages.LRRMessage`
        """
        status = self._get_event_status(message)
        if status is None:
            return

        if message.event_code in LRR_FIRE_EVENTS:
            if message.event_code == LRR_CID_EVENT.OPENCLOSE_CANCEL_BY_USER:
                status = False

            self._alarmdecoder._update_fire_status(status=status)
            
        if message.event_code in LRR_ALARM_EVENTS:
            kwargs = {}
            field_name = 'zone'
            if not status:
                field_name = 'user'

            kwargs[field_name] = int(message.event_data)
            self._alarmdecoder._update_alarm_status(status=status, **kwargs)

        if message.event_code in LRR_POWER_EVENTS:
            self._alarmdecoder._update_power_status(status=status)

        if message.event_code in LRR_BYPASS_EVENTS:
            self._alarmdecoder._update_zone_bypass_status(status=status, zone=int(message.event_data))

        if message.event_code in LRR_BATTERY_EVENTS:
            self._alarmdecoder._update_battery_status(status=status)

        if message.event_code in LRR_PANIC_EVENTS:
            if message.event_code == LRR_CID_EVENT.OPENCLOSE_CANCEL_BY_USER:
                status = False

            self._alarmdecoder._update_panic_status(status=status)

        if message.event_code in LRR_ARM_EVENTS:
            # NOTE: status on OPENCLOSE messages is backwards.
            status_stay = (message.event_status == LRR_EVENT_STATUS.RESTORE \
                            and message.event_code in LRR_STAY_EVENTS)

            if status_stay:
                status = False
            else:
                status = not status

            self._alarmdecoder._update_armed_status(status=status, status_stay=status_stay)

    def _handle_dsc_message(self, message):
        """
        Handles DSC LRR events.

        :param message: LRR message object
        :type message: :py:class:`~alarmdecoder.messages.LRRMessage`
        """
        pass

    def _handle_ademco_message(self, message):
        """
        Handles ADEMCO LRR events.

        :param message: LRR message object
        :type message: :py:class:`~alarmdecoder.messages.LRRMessage`
        """
        pass

    def _handle_alarmdecoder_message(self, message):
        """
        Handles AlarmDecoder LRR events.

        :param message: LRR message object
        :type message: :py:class:`~alarmdecoder.messages.LRRMessage`
        """
        pass

    def _handle_unknown_message(self, message):
        """
        Handles UNKNOWN LRR events.

        :param message: LRR message object
        :type message: :py:class:`~alarmdecoder.messages.LRRMessage`
        """
        # TODO: Log this somewhere useful.
        pass

    def _get_event_status(self, message):
        """
        Retrieves the boolean status of an LRR message.

        :param message: LRR message object
        :type message: :py:class:`~alarmdecoder.messages.LRRMessage`

        :returns: Boolean indicating whether the event was triggered or restored.
        """
        status = None

        if message.event_status == LRR_EVENT_STATUS.TRIGGER:
            status = True
        elif message.event_status == LRR_EVENT_STATUS.RESTORE:
            status = False

        return status
