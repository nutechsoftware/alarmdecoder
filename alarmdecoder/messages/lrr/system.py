
from .events import LRR_EVENT_TYPE, LRR_EVENT_STATUS, LRR_CID_EVENT
from .events import LRR_FIRE_EVENTS, LRR_POWER_EVENTS, LRR_BYPASS_EVENTS, LRR_BATTERY_EVENTS, \
                    LRR_PANIC_EVENTS, LRR_ARM_EVENTS, LRR_STAY_EVENTS


class LRRSystem(object):
    def __init__(self, alarmdecoder_object):
        self._alarmdecoder = alarmdecoder_object

    def update(self, message):
        handled = False

        print("LRR Message: {0}".format(message.dict()))

        source = message.event_source
        if source == LRR_EVENT_TYPE.CID:
            handled = self._handle_cid_message(message)
        elif source == LRR_EVENT_TYPE.DSC:
            handled = self._handle_dsc_message(message)
        elif source == LRR_EVENT_TYPE.ADEMCO:
            handled = self._handle_ademco_message(message)
        elif source == LRR_EVENT_TYPE.ALARMDECODER:
            handled = self._handle_alarmdecoder_message(message)
        elif source == LRR_EVENT_TYPE.UNKNOWN:
            handled = self._handle_unknown_message(message)
        else:
            pass

        return handled

    def _handle_cid_message(self, message):
        handled = True

        status = self._get_event_status(message)
        if status is None:
            print("Unknown LRR event status: {0}".format(message))
            return

        if message.event_code in LRR_FIRE_EVENTS:
            self._alarmdecoder._update_fire_status(status=status)
        elif message.event_code in LRR_POWER_EVENTS:
            self._alarmdecoder._update_power_status(status=status)
        elif message.event_code in LRR_BYPASS_EVENTS:
            self._alarmdecoder._update_zone_bypass_status(status=status)
        elif message.event_code in LRR_BATTERY_EVENTS:
            self._alarmdecoder._update_battery_status(status=status)
        elif message.event_code in LRR_PANIC_EVENTS:
            if message.event_code == LRR_CID_EVENT.OPENCLOSE_CANCEL_BY_USER:
                status = False

            self._alarmdecoder._update_panic_status(status=status)
        elif message.event_code in LRR_ARM_EVENTS:
            # NOTE: status on OPENCLOSE messages is backwards.
            status_stay = (message.event_status == LRR_EVENT_STATUS.RESTORE \
                            and message.event_code in LRR_STAY_EVENTS)
            self._alarmdecoder._update_armed_status(status=not status, status_stay=status_stay)
        else:
            handled = False

        return handled

    def _handle_dsc_message(self, message):
        return False

    def _handle_ademco_message(self, message):
        return False

    def _handle_alarmdecoder_message(self, message):
        return False

    def _handle_unknown_message(self, message):
        # TODO: Log this somewhere useful.
        print("UNKNOWN LRR EVENT: {0}".format(message))

        return False

    def _get_event_status(self, message):
        status = None

        if message.event_status == LRR_EVENT_STATUS.TRIGGER:
            status = True
        elif message.event_status == LRR_EVENT_STATUS.RESTORE:
            status = False

        return status
