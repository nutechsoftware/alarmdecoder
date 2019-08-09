"""
Provides the main AlarmDecoder class.

.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import sys
import time
import re

try:
    from builtins import chr
except ImportError:
    pass

from .event import event
from .util import InvalidMessageError
from .messages import Message, ExpanderMessage, RFMessage, LRRMessage, AUIMessage
from .messages.lrr import LRRSystem
from .zonetracking import Zonetracker
from .panels import PANEL_TYPES, ADEMCO, DSC
from .states import FireState


class AlarmDecoder(object):
    """
    High-level wrapper around `AlarmDecoder`_ (AD2) devices.
    """

    # High-level Events
    on_arm = event.Event("This event is called when the panel is armed.\n\n**Callback definition:** *def callback(device, stay)*")
    on_disarm = event.Event("This event is called when the panel is disarmed.\n\n**Callback definition:** *def callback(device)*")
    on_power_changed = event.Event("This event is called when panel power switches between AC and DC.\n\n**Callback definition:** *def callback(device, status)*")
    on_ready_changed = event.Event("This event is called when panel ready state changes.\n\n**Callback definition:** *def callback(device, status)*")
    on_alarm = event.Event("This event is called when the alarm is triggered.\n\n**Callback definition:** *def callback(device, zone)*")
    on_alarm_restored = event.Event("This event is called when the alarm stops sounding.\n\n**Callback definition:** *def callback(device, zone)*")
    on_fire = event.Event("This event is called when a fire is detected.\n\n**Callback definition:** *def callback(device, status)*")
    on_bypass = event.Event("This event is called when a zone is bypassed.  \n\n\n\n**Callback definition:** *def callback(device, status)*")
    on_boot = event.Event("This event is called when the device finishes booting.\n\n**Callback definition:** *def callback(device)*")
    on_config_received = event.Event("This event is called when the device receives its configuration. \n\n**Callback definition:** *def callback(device)*")
    on_zone_fault = event.Event("This event is called when :py:class:`~alarmdecoder.zonetracking.Zonetracker` detects a zone fault.\n\n**Callback definition:** *def callback(device, zone)*")
    on_zone_restore = event.Event("This event is called when :py:class:`~alarmdecoder.zonetracking.Zonetracker` detects that a fault is restored.\n\n**Callback definition:** *def callback(device, zone)*")
    on_low_battery = event.Event("This event is called when the device detects a low battery.\n\n**Callback definition:** *def callback(device, status)*")
    on_panic = event.Event("This event is called when the device detects a panic.\n\n**Callback definition:** *def callback(device, status)*")
    on_relay_changed = event.Event("This event is called when a relay is opened or closed on an expander board.\n\n**Callback definition:** *def callback(device, message)*")
    on_chime_changed = event.Event("This event is called when chime state changes.\n\n**Callback definition:** *def callback(device, message)*")

    # Mid-level Events
    on_message = event.Event("This event is called when standard panel :py:class:`~alarmdecoder.messages.Message` is received.\n\n**Callback definition:** *def callback(device, message)*")
    on_expander_message = event.Event("This event is called when an :py:class:`~alarmdecoder.messages.ExpanderMessage` is received.\n\n**Callback definition:** *def callback(device, message)*")
    on_lrr_message = event.Event("This event is called when an :py:class:`~alarmdecoder.messages.LRRMessage` is received.\n\n**Callback definition:** *def callback(device, message)*")
    on_rfx_message = event.Event("This event is called when an :py:class:`~alarmdecoder.messages.RFMessage` is received.\n\n**Callback definition:** *def callback(device, message)*")
    on_sending_received = event.Event("This event is called when a !Sending.done message is received from the AlarmDecoder.\n\n**Callback definition:** *def callback(device, status, message)*")
    on_aui_message = event.Event("This event is called when an :py:class`~alarmdecoder.messages.AUIMessage` is received\n\n**Callback definition:** *def callback(device, message)*")

    # Low-level Events
    on_open = event.Event("This event is called when the device has been opened.\n\n**Callback definition:** *def callback(device)*")
    on_close = event.Event("This event is called when the device has been closed.\n\n**Callback definition:** *def callback(device)*")
    on_read = event.Event("This event is called when a line has been read from the device.\n\n**Callback definition:** *def callback(device, data)*")
    on_write = event.Event("This event is called when data has been written to the device.\n\n**Callback definition:** *def callback(device, data)*")

    # Constants
    KEY_F1 = chr(1) + chr(1) + chr(1)
    """Represents panel function key #1"""
    KEY_F2 = chr(2) + chr(2) + chr(2)
    """Represents panel function key #2"""
    KEY_F3 = chr(3) + chr(3) + chr(3)
    """Represents panel function key #3"""
    KEY_F4 = chr(4) + chr(4) + chr(4)
    """Represents panel function key #4"""
    KEY_PANIC = chr(2) + chr(2) + chr(2)
    """Represents a panic keypress"""
    KEY_S1 = chr(1) + chr(1) + chr(1)
    """Represents panel special key #1"""
    KEY_S2 = chr(2) + chr(2) + chr(2)
    """Represents panel special key #2"""
    KEY_S3 = chr(3) + chr(3) + chr(3)
    """Represents panel special key #3"""
    KEY_S4 = chr(4) + chr(4) + chr(4)
    """Represents panel special key #4"""
    KEY_S5 = chr(5) + chr(5) + chr(5)
    """Represents panel special key #5"""
    KEY_S6 = chr(6) + chr(6) + chr(6)
    """Represents panel special key #6"""
    KEY_S7 = chr(7) + chr(7) + chr(7)
    """Represents panel special key #7"""
    KEY_S8 = chr(8) + chr(8) + chr(8)
    """Represents panel special key #8"""



    BATTERY_TIMEOUT = 30
    """Default timeout (in seconds) before the battery status reverts."""
    FIRE_TIMEOUT = 30
    """Default tTimeout (in seconds) before the fire status reverts."""

    # Attributes
    address = 18
    """The keypad address in use by the device."""
    configbits = 0xFF00
    """The configuration bits set on the device."""
    address_mask = 0xFFFFFFFF
    """The address mask configured on the device."""
    emulate_zone = [False for _ in list(range(5))]
    """List containing the devices zone emulation status."""
    emulate_relay = [False for _ in list(range(4))]
    """List containing the devices relay emulation status."""
    emulate_lrr = False
    """The status of the devices LRR emulation."""
    deduplicate = False
    """The status of message deduplication as configured on the device."""
    mode = ADEMCO
    """The panel mode that the AlarmDecoder is in.  Currently supports ADEMCO and DSC."""
    emulate_com = False
    """The status of the devices COM emulation."""

    #Version Information
    serial_number = 'Unknown'
    """The device serial number"""
    version_number = 'Unknown'
    """The device firmware version"""
    version_flags = ""
    """Device flags enabled"""

    def __init__(self, device, ignore_message_states=False, ignore_lrr_states=True):
        """
        Constructor

        :param device: The low-level device used for this `AlarmDecoder`_
                       interface.
        :type device: Device
        :param ignore_message_states: Ignore regular panel messages when updating internal states
        :type ignore_message_states: bool
        :param ignore_lrr_states: Ignore LRR panel messages when updating internal states
        :type ignore_lrr_states: bool
        """
        self._device = device
        self._zonetracker = Zonetracker(self)
        self._lrr_system = LRRSystem(self)

        self._ignore_message_states = ignore_message_states
        self._ignore_lrr_states = ignore_lrr_states
        self._battery_timeout = AlarmDecoder.BATTERY_TIMEOUT
        self._fire_timeout = AlarmDecoder.FIRE_TIMEOUT
        self._power_status = None
        self._chime_status = None
        self._ready_status = None
        self._alarm_status = None
        self._bypass_status = {}
        self._armed_status = None
        self._entry_delay_off_status = None
        self._perimeter_only_status = None
        self._armed_stay = False
        self._exit = False
        self._fire_status = False
        self._fire_status_timeout = 0
        self._battery_status = (False, 0)
        self._panic_status = False
        self._relay_status = {}
        self._internal_address_mask = 0xFFFFFFFF

        self.last_fault_expansion = 0
        self.fault_expansion_time_limit = 30  # Seconds

        self.address = 18
        self.configbits = 0xFF00
        self.address_mask = 0xFFFFFFFF
        self.emulate_zone = [False for x in list(range(5))]
        self.emulate_relay = [False for x in list(range(4))]
        self.emulate_lrr = False
        self.deduplicate = False
        self.mode = ADEMCO
        self.emulate_com = False

        self.serial_number = 'Unknown'
        self.version_number = 'Unknown'
        self.version_flags = ""

    def __enter__(self):
        """
        Support for context manager __enter__.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Support for context manager __exit__.
        """
        self.close()

        return False

    @property
    def id(self):
        """
        The ID of the `AlarmDecoder`_ device.

        :returns: identification string for the device
        """
        return self._device.id

    @property
    def battery_timeout(self):
        """
        Retrieves the timeout for restoring the battery status, in seconds.

        :returns: battery status timeout
        """
        return self._battery_timeout

    @battery_timeout.setter
    def battery_timeout(self, value):
        """
        Sets the timeout for restoring the battery status, in seconds.

        :param value: timeout in seconds
        :type value: int
        """
        self._battery_timeout = value

    @property
    def fire_timeout(self):
        """
        Retrieves the timeout for restoring the fire status, in seconds.

        :returns: fire status timeout
        """
        return self._fire_timeout

    @fire_timeout.setter
    def fire_timeout(self, value):
        """
        Sets the timeout for restoring the fire status, in seconds.

        :param value: timeout in seconds
        :type value: int
        """
        self._fire_timeout = value

    @property
    def internal_address_mask(self):
        """
        Retrieves the address mask used for updating internal status.

        :returns: address mask
        """
        return self._internal_address_mask

    @internal_address_mask.setter
    def internal_address_mask(self, value):
        """
        Sets the address mask used internally for updating status.

        :param value: address mask
        :type value: int
        """
        self._internal_address_mask = value

    def open(self, baudrate=None, no_reader_thread=False):
        """Opens the device.

        If the device cannot be opened, an exception is thrown.  In that
        case, open() can be called repeatedly to try and open the
        connection.

        :param baudrate: baudrate used for the device.  Defaults to the lower-level device default.
        :type baudrate: int
        :param no_reader_thread: Specifies whether or not the automatic reader
                                 thread should be started.
        :type no_reader_thread: bool
        """
        self._wire_events()
        try:
            self._device.open(baudrate=baudrate,
                              no_reader_thread=no_reader_thread)
        except:
            self._unwire_events
            raise

        return self

    def close(self):
        """
        Closes the device.
        """
        self._device.close()
        self._unwire_events()

    def send(self, data):
        """
        Sends data to the `AlarmDecoder`_ device.

        :param data: data to send
        :type data: string
        """

        if self._device:
            if isinstance(data, str):
                data = str.encode(data)

            # Hack to support unicode under Python 2.x
            if sys.version_info < (3,):
                if isinstance(data, unicode):
                    data = bytes(data)

            self._device.write(data)

    def get_config(self):
        """
        Retrieves the configuration from the device.  Called automatically by :py:meth:`_on_open`.
        """
        self.send("C\r")

    def save_config(self):
        """
        Sets configuration entries on the device.
        """
        self.send("C{0}\r".format(self.get_config_string()))

    def get_config_string(self):
        """
        Build a configuration string that's compatible with the AlarmDecoder configuration
        command from the current values in the object.

        :returns: string
        """
        config_entries = []

        # HACK: This is ugly.. but I can't think of an elegant way of doing it.
        config_entries.append(('ADDRESS', '{0}'.format(self.address)))
        config_entries.append(('CONFIGBITS', '{0:x}'.format(self.configbits)))
        config_entries.append(('MASK', '{0:x}'.format(self.address_mask)))
        config_entries.append(('EXP',
                               ''.join(['Y' if z else 'N' for z in self.emulate_zone])))
        config_entries.append(('REL',
                               ''.join(['Y' if r else 'N' for r in self.emulate_relay])))
        config_entries.append(('LRR', 'Y' if self.emulate_lrr else 'N'))
        config_entries.append(('DEDUPLICATE', 'Y' if self.deduplicate else 'N'))
        config_entries.append(('MODE', list(PANEL_TYPES)[list(PANEL_TYPES.values()).index(self.mode)]))
        config_entries.append(('COM', 'Y' if self.emulate_com else 'N'))

        config_string = '&'.join(['='.join(t) for t in config_entries])

        return '&'.join(['='.join(t) for t in config_entries])

    def get_version(self):
        """
        Retrieves the version string from the device.  Called automatically by :py:meth:`_on_open`.
        """
        self.send("V\r")

    def reboot(self):
        """
        Reboots the device.
        """
        self.send('=')

    def fault_zone(self, zone, simulate_wire_problem=False):
        """
        Faults a zone if we are emulating a zone expander.

        :param zone: zone to fault
        :type zone: int
        :param simulate_wire_problem: Whether or not to simulate a wire fault
        :type simulate_wire_problem: bool
        """

        # Allow ourselves to also be passed an address/channel combination
        # for zone expanders.
        #
        # Format (expander index, channel)
        if isinstance(zone, tuple):
            expander_idx, channel = zone

            zone = self._zonetracker.expander_to_zone(expander_idx, channel)

        status = 2 if simulate_wire_problem else 1

        self.send("L{0:02}{1}\r".format(zone, status))

    def clear_zone(self, zone):
        """
        Clears a zone if we are emulating a zone expander.

        :param zone: zone to clear
        :type zone: int
        """
        self.send("L{0:02}0\r".format(zone))

    def _wire_events(self):
        """
        Wires up the internal device events.
        """
        self._device.on_open += self._on_open
        self._device.on_close += self._on_close
        self._device.on_read += self._on_read
        self._device.on_write += self._on_write
        self._zonetracker.on_fault += self._on_zone_fault
        self._zonetracker.on_restore += self._on_zone_restore

    def _unwire_events(self):
        """
        Wires up the internal device events.
        """
        self._device.on_open -= self._on_open
        self._device.on_close -= self._on_close
        self._device.on_read -= self._on_read
        self._device.on_write -= self._on_write
        self._zonetracker.on_fault -= self._on_zone_fault
        self._zonetracker.on_restore -= self._on_zone_restore

    def _handle_message(self, data):
        """
        Parses keypad messages from the panel.

        :param data: keypad data to parse
        :type data: string

        :returns: :py:class:`~alarmdecoder.messages.Message`
        """

        try:
            data = data.decode('utf-8')
        except:
            raise InvalidMessageError('Decode failed for message: {0}'.format(data))

        if data is not None:
            data = data.lstrip('\0')

        if data is None or data == '':
            raise InvalidMessageError()

        msg = None
        header = data[0:4]

        if header[0] != '!' or header == '!KPM':
            msg = self._handle_keypad_message(data)

        elif header == '!EXP' or header == '!REL':
            msg = self._handle_expander_message(data)

        elif header == '!RFX':
            msg = self._handle_rfx(data)

        elif header == '!LRR':
            msg = self._handle_lrr(data)

        elif header == '!AUI':
            msg = self._handle_aui(data)

        elif data.startswith('!Ready'):
            self.on_boot()

        elif data.startswith('!CONFIG'):
            self._handle_config(data)

        elif data.startswith('!VER'):
            self._handle_version(data)

        elif data.startswith('!Sending'):
            self._handle_sending(data)

        return msg

    def _handle_keypad_message(self, data):
        """
        Handle keypad messages.

        :param data: keypad message to parse
        :type data: string

        :returns: :py:class:`~alarmdecoder.messages.Message`
        """

        msg = Message(data)

        if self._internal_address_mask & msg.mask > 0:
            if not self._ignore_message_states:
                self._update_internal_states(msg)

            self.on_message(message=msg)

        return msg

    def _handle_expander_message(self, data):
        """
        Handle expander messages.

        :param data: expander message to parse
        :type data: string

        :returns: :py:class:`~alarmdecoder.messages.ExpanderMessage`
        """
        msg = ExpanderMessage(data)

        self._update_internal_states(msg)
        self.on_expander_message(message=msg)

        return msg

    def _handle_rfx(self, data):
        """
        Handle RF messages.

        :param data: RF message to parse
        :type data: string

        :returns: :py:class:`~alarmdecoder.messages.RFMessage`
        """
        msg = RFMessage(data)

        self.on_rfx_message(message=msg)

        return msg

    def _handle_lrr(self, data):
        """
        Handle Long Range Radio messages.

        :param data: LRR message to parse
        :type data: string

        :returns: :py:class:`~alarmdecoder.messages.LRRMessage`
        """
        msg = LRRMessage(data)

        if not self._ignore_lrr_states:
            self._lrr_system.update(msg)
        self.on_lrr_message(message=msg)

        return msg

    def _handle_aui(self, data):
        """
        Handle AUI messages.

        :param data: RF message to parse
        :type data: string

        :returns: :py:class`~alarmdecoder.messages.AUIMessage`
        """
        msg = AUIMessage(data)

        self.on_aui_message(message=msg)

        return msg

    def _handle_version(self, data):
        """
        Handles received version data.

        :param data: Version string to parse
        :type data: string
        """

        _, version_string = data.split(':')
        version_parts = version_string.split(',')

        self.serial_number = version_parts[0]
        self.version_number = version_parts[1]
        self.version_flags = version_parts[2]

    def _handle_config(self, data):
        """
        Handles received configuration data.

        :param data: Configuration string to parse
        :type data: string
        """
        _, config_string = data.split('>')
        for setting in config_string.split('&'):
            key, val = setting.split('=')

            if key == 'ADDRESS':
                self.address = int(val)
            elif key == 'CONFIGBITS':
                self.configbits = int(val, 16)
            elif key == 'MASK':
                self.address_mask = int(val, 16)
            elif key == 'EXP':
                self.emulate_zone = [val[z] == 'Y' for z in list(range(5))]
            elif key == 'REL':
                self.emulate_relay = [val[r] == 'Y' for r in list(range(4))]
            elif key == 'LRR':
                self.emulate_lrr = (val == 'Y')
            elif key == 'DEDUPLICATE':
                self.deduplicate = (val == 'Y')
            elif key == 'MODE':
                self.mode = PANEL_TYPES[val]
            elif key == 'COM':
                self.emulate_com = (val == 'Y')

        self.on_config_received()

    def _handle_sending(self, data):
        """
        Handles results of a keypress send.

        :param data: Sending string to parse
        :type data: string
        """

        matches = re.match('^!Sending(\.{1,5})done.*', data)
        if matches is not None:
            good_send = False
            if len(matches.group(1)) < 5:
                good_send = True

            self.on_sending_received(status=good_send, message=data)

    def _update_internal_states(self, message):
        """
        Updates internal device states.

        :param message: :py:class:`~alarmdecoder.messages.Message` to update internal states with
        :type message: :py:class:`~alarmdecoder.messages.Message`, :py:class:`~alarmdecoder.messages.ExpanderMessage`, :py:class:`~alarmdecoder.messages.LRRMessage`, or :py:class:`~alarmdecoder.messages.RFMessage`
        """
        if isinstance(message, Message) and not self._ignore_message_states:
            self._update_armed_ready_status(message)
            self._update_power_status(message)
            self._update_chime_status(message)
            self._update_alarm_status(message)
            self._update_zone_bypass_status(message)
            self._update_battery_status(message)
            self._update_fire_status(message)

        elif isinstance(message, ExpanderMessage):
            self._update_expander_status(message)

        self._update_zone_tracker(message)

    def _update_power_status(self, message=None, status=None):
        """
        Uses the provided message to update the AC power state.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`
        :param status: power status, overrides message bits.
        :type status: bool

        :returns: bool indicating the new status
        """
        power_status = status
        if isinstance(message, Message):
            power_status = message.ac_power

        if power_status is None:
            return

        if power_status != self._power_status:
            self._power_status, old_status = power_status, self._power_status

            if old_status is not None:
                self.on_power_changed(status=self._power_status)

        return self._power_status

    def _update_chime_status(self, message=None, status=None):
        """
        Uses the provided message to update the Chime state.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`
        :param status: chime status, overrides message bits.
        :type status: bool

        :returns: bool indicating the new status
        """
        chime_status = status
        if isinstance(message, Message):
            chime_status = message.chime_on

        if chime_status is None:
            return

        if chime_status != self._chime_status:
            self._chime_status, old_status = chime_status, self._chime_status

            if old_status is not None:
                self.on_chime_changed(status=self._chime_status)

        return self._chime_status

    def _update_alarm_status(self, message=None, status=None, zone=None, user=None):
        """
        Uses the provided message to update the alarm state.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`
        :param status: alarm status, overrides message bits.
        :type status: bool
        :param user: user associated with alarm event
        :type user: string

        :returns: bool indicating the new status
        """

        alarm_status = status
        alarm_zone = zone
        if isinstance(message, Message):
            alarm_status = message.alarm_sounding
            alarm_zone = message.parse_numeric_code()

        if alarm_status != self._alarm_status:
            self._alarm_status, old_status = alarm_status, self._alarm_status

            if old_status is not None or status is not None:
                if self._alarm_status:
                    self.on_alarm(zone=alarm_zone)
                else:
                    self.on_alarm_restored(zone=alarm_zone, user=user)

        return self._alarm_status

    def _update_zone_bypass_status(self, message=None, status=None, zone=None):
        """
        Uses the provided message to update the zone bypass state.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`
        :param status: bypass status, overrides message bits.
        :type status: bool
        :param zone: zone associated with bypass event
        :type zone: int

        :returns: dictionary {Zone:True|False,...}
           Zone can be None if LRR CID Bypass checking is disabled
           or we do not know what zones but know something is bypassed.
        """
        bypass_status = status
        if isinstance(message, Message):
            bypass_status = message.zone_bypassed

        if bypass_status is None:
            return

        old_bypass_status = self._bypass_status.get(zone, None)

        if bypass_status != old_bypass_status:
            if bypass_status == False and zone is None:
                self._bypass_status = {}
            else:
                self._bypass_status[zone] = bypass_status

            if old_bypass_status is not None or message is None or (old_bypass_status is None and bypass_status is True):
                self.on_bypass(status=bypass_status, zone=zone)

        return bypass_status

    def _update_armed_ready_status(self, message=None):
        """
        Uses the provided message to update the armed state
        and ready state at once as they can change in the same
        message and we want both events to have the same states.
        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`

        """

        arm_status = None
        stay_status = None
        exit = None
        ready_status = None
        entry_delay_off_status = None
        perimeter_only_status = None
        send_ready = False
        send_arm = False

        if isinstance(message, Message):
            arm_status = message.armed_away
            stay_status = message.armed_home
            ready_status = message.ready
            entry_delay_off_status = message.entry_delay_off
            perimeter_only_status = message.perimeter_only

        if arm_status is None or stay_status is None or ready_status is None:
            return

        # if we are armed we may be in exit mode
        if arm_status or stay_status:
            exit = False
            messageUp = message.text.upper()

            if self.mode == ADEMCO:
                # skip these messages
                if not messageUp.startswith("SYSTEM") and not messageUp.startswith("CHECK"):
                    if "MAY EXIT NOW" in messageUp:
                        exit = True
                else:
                    # preserve last state
                    exit = self._exit

            if self.mode == DSC:
                if any(s in messageUp for s in ("QUICK EXIT", "EXIT DELAY")):
                    exit = True
        else:
            exit = False

        self._armed_stay, old_stay = stay_status, self._armed_stay
        self._armed_status, old_arm = arm_status, self._armed_status
        self._ready_status, old_ready_status = ready_status, self._ready_status
        self._entry_delay_off_status, old_entry_delay_off_status = entry_delay_off_status, self._entry_delay_off_status
        self._perimeter_only_status, old_perimeter_only_status = perimeter_only_status, self._perimeter_only_status
        self._exit, old_exit = exit, self._exit

        if old_arm is not None:
            if arm_status != old_arm or stay_status != old_stay:
                send_arm = True

        # This bit is expected to change only when the ARMED bit changes.
        # But just in case watch for it to change
        if old_entry_delay_off_status is not None:
            if entry_delay_off_status != old_entry_delay_off_status:
                send_ready = True

        # This bit can change after the armed bit is set
        # this will treat it like AWAY/Stay transition as an additional
        # arming event.
        if old_perimeter_only_status is not None:
            if perimeter_only_status != old_perimeter_only_status:
                send_ready = True

        if old_ready_status is not None:
            if ready_status != old_ready_status:
                send_ready = True

        # Send exist status updates in ready event
        if old_exit is not None:
            if exit != old_exit:
                send_ready = True

        if send_ready:
            self.on_ready_changed(status=self._ready_status)

        if send_arm:
            if self._armed_status or self._armed_stay:
                self.on_arm(stay=stay_status)
            else:
                self.on_disarm()

    def _update_armed_status(self, message=None, status=None, status_stay=None):
        """
        Uses the provided message to update the armed state.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`
        :param status: armed status, overrides message bits
        :type status: bool
        :param status_stay: armed stay status, overrides message bits
        :type status_stay: bool

        :returns: bool indicating the new status
        """
        arm_status = status
        stay_status = status_stay

        if isinstance(message, Message):
            arm_status = message.armed_away
            stay_status = message.armed_home

        if arm_status is None or stay_status is None:
            return

        self._armed_status, old_status = arm_status, self._armed_status
        self._armed_stay, old_stay = stay_status, self._armed_stay
        if arm_status != old_status or stay_status != old_stay:
            if old_status is not None or message is None:
                if self._armed_status or self._armed_stay:
                    self.on_arm(stay=stay_status)
                else:
                    self.on_disarm()

        return self._armed_status or self._armed_stay

    def _update_battery_status(self, message=None, status=None):
        """
        Uses the provided message to update the battery state.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`
        :param status: battery status, overrides message bits
        :type status: bool

        :returns: boolean indicating the new status
        """
        battery_status = status
        if isinstance(message, Message):
            battery_status = message.battery_low

        if battery_status is None:
            return

        last_status, last_update = self._battery_status
        if battery_status == last_status:
            self._battery_status = (last_status, time.time())
        else:
            if battery_status is True or time.time() > last_update + self._battery_timeout:
                self._battery_status = (battery_status, time.time())
                self.on_low_battery(status=battery_status)

        return self._battery_status[0]

    def _update_fire_status(self, message=None, status=None):
        """
        Uses the provided message to update the fire alarm state.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`
        :param status: fire status, overrides message bits
        :type status: bool

        :returns: boolean indicating the new status
        """
        fire_status = status

        last_status  = self._fire_status
        last_update = self._fire_status_timeout

        # Quirk in Ademco panels. Fire bit goes on/off if other alarms are on or a system fault
        if isinstance(message, Message):
            if self.mode == ADEMCO:
                # if we did not have an alarm and we do now send event
                if message.fire_alarm and message.fire_alarm != self._fire_status:
                    fire_status = message.fire_alarm

                # if we had an alarm and the sticky bit was cleared then clear the alarm
                ## ignore sticky bit on these messages :(
                if (not message.text.startswith("SYSTEM") and
                    not message.text.startswith("CHECK")):
                    if self._fire_status and not message.alarm_event_occurred:
                        # fire restore
                        fire_status = False

                # if we had a fire event and it went away and we still have a sticky alarm bit
                # then it is not gone yet just restore it
                if not message.fire_alarm and self._fire_status:
                    if message.alarm_event_occurred:
                        fire_status = self._fire_status

                # if we had an alarm already and we get it again extend the timeout
                if message.fire_alarm and message.fire_alarm == self._fire_status:
                    self._fire_status = message.fire_alarm
                    self._fire_status_timeout = time.time()

                # if we timeout with an alarm set restore it
                if self._fire_status:
                    if time.time() > last_update + self._fire_timeout:
                        fire_status = False

            else:
                fire_status = message.fire_alarm

        if fire_status != self._fire_status:
            if fire_status is not None:
                self._fire_status = fire_status
                self._fire_status_timeout = time.time()
                self.on_fire(status=fire_status)

        return self._fire_status

    def _update_panic_status(self, status=None):
        """
        Updates the panic status of the alarm panel.

        :param status: status to use to update
        :type status: boolean

        :returns: boolean indicating the new status
        """
        if status is None:
            return

        if status != self._panic_status:
            self._panic_status, old_status = status, self._panic_status

            if old_status is not None:
                self.on_panic(status=self._panic_status)

        return self._panic_status

    def _update_expander_status(self, message):
        """
        Uses the provided message to update the expander states.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.ExpanderMessage`

        :returns: boolean indicating the new status
        """

        if message.type == ExpanderMessage.RELAY:
            self._relay_status[(message.address, message.channel)] = message.value

            self.on_relay_changed(message=message)

            return self._relay_status[(message.address, message.channel)]

    def _update_zone_tracker(self, message):
        """
        Trigger an update of the :py:class:`~alarmdecoder.messages.Zonetracker`.

        :param message: message to update the zonetracker with
        :type message: :py:class:`~alarmdecoder.messages.Message`, :py:class:`~alarmdecoder.messages.ExpanderMessage`, :py:class:`~alarmdecoder.messages.LRRMessage`, or :py:class:`~alarmdecoder.messages.RFMessage`
        """

        # Retrieve a list of faults.
        # NOTE: This only happens on first boot or after exiting programming mode.
        if isinstance(message, Message):
            if not message.ready and ("Hit * for faults" in message.text or "Press *  to show faults" in message.text):
                if time.time() > self.last_fault_expansion + self.fault_expansion_time_limit:
                    self.last_fault_expansion = time.time()
                    self.send('*')
                    return

        self._zonetracker.update(message)

    def _on_open(self, sender, *args, **kwargs):
        """
        Internal handler for opening the device.
        """
        self.get_config()
        self.get_version()

        self.on_open()

    def _on_close(self, sender, *args, **kwargs):
        """
        Internal handler for closing the device.
        """
        self.on_close()

    def _on_read(self, sender, *args, **kwargs):
        """
        Internal handler for reading from the device.
        """
        data = kwargs.get('data', None)
        self.on_read(data=data)

        self._handle_message(data)

    def _on_write(self, sender, *args, **kwargs):
        """
        Internal handler for writing to the device.
        """
        self.on_write(data=kwargs.get('data', None))

    def _on_zone_fault(self, sender, *args, **kwargs):
        """
        Internal handler for zone faults.
        """
        self.on_zone_fault(*args, **kwargs)

    def _on_zone_restore(self, sender, *args, **kwargs):
        """
        Internal handler for zone restoration.
        """
        self.on_zone_restore(*args, **kwargs)
