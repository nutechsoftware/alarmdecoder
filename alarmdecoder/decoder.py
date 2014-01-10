"""
Provides the main AlarmDecoder class.

.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import time

from .event import event
from .util import InvalidMessageError
from .messages import Message, ExpanderMessage, RFMessage, LRRMessage
from .zonetracking import Zonetracker


class AlarmDecoder(object):
    """
    High-level wrapper around `AlarmDecoder`_ (AD2) devices.
    """

    # High-level Events
    on_arm = event.Event("This event is called when the panel is armed.\n\n**Callback definition:** *def callback(device)*")
    on_disarm = event.Event("This event is called when the panel is disarmed.\n\n**Callback definition:** *def callback(device)*")
    on_power_changed = event.Event("This event is called when panel power switches between AC and DC.\n\n**Callback definition:** *def callback(device, status)*")
    on_alarm = event.Event("This event is called when the alarm is triggered.\n\n**Callback definition:** *def callback(device, status)*")
    on_fire = event.Event("This event is called when a fire is detected.\n\n**Callback definition:** *def callback(device, status)*")
    on_bypass = event.Event("This event is called when a zone is bypassed.  \n\n\n\n**Callback definition:** *def callback(device, status)*")
    on_boot = event.Event("This event is called when the device finishes booting.\n\n**Callback definition:** *def callback(device)*")
    on_config_received = event.Event("This event is called when the device receives its configuration. \n\n**Callback definition:** *def callback(device)*")
    on_zone_fault = event.Event("This event is called when :py:class:`~alarmdecoder.zonetracking.Zonetracker` detects a zone fault.\n\n**Callback definition:** *def callback(device, zone)*")
    on_zone_restore = event.Event("This event is called when :py:class:`~alarmdecoder.zonetracking.Zonetracker` detects that a fault is restored.\n\n**Callback definition:** *def callback(device, zone)*")
    on_low_battery = event.Event("This event is called when the device detects a low battery.\n\n**Callback definition:** *def callback(device, status)*")
    on_panic = event.Event("This event is called when the device detects a panic.\n\n**Callback definition:** *def callback(device, status)*")
    on_relay_changed = event.Event("This event is called when a relay is opened or closed on an expander board.\n\n**Callback definition:** *def callback(device, message)*")

    # Mid-level Events
    on_message = event.Event("This event is called when standard panel :py:class:`~alarmdecoder.messages.Message` is received.\n\n**Callback definition:** *def callback(device, message)*")
    on_expander_message = event.Event("This event is called when an :py:class:`~alarmdecoder.messages.ExpanderMessage` is received.\n\n**Callback definition:** *def callback(device, message)*")
    on_lrr_message = event.Event("This event is called when an :py:class:`~alarmdecoder.messages.LRRMessage` is received.\n\n**Callback definition:** *def callback(device, message)*")
    on_rfx_message = event.Event("This event is called when an :py:class:`~alarmdecoder.messages.RFMessage` is received.\n\n**Callback definition:** *def callback(device, message)*")

    # Low-level Events
    on_open = event.Event("This event is called when the device has been opened.\n\n**Callback definition:** *def callback(device)*")
    on_close = event.Event("This event is called when the device has been closed.\n\n**Callback definition:** *def callback(device)*")
    on_read = event.Event("This event is called when a line has been read from the device.\n\n**Callback definition:** *def callback(device, data)*")
    on_write = event.Event("This event is called when data has been written to the device.\n\n**Callback definition:** *def callback(device, data)*")

    # Constants
    KEY_F1 = unichr(1) + unichr(1) + unichr(1)
    """Represents panel function key #1"""
    KEY_F2 = unichr(2) + unichr(2) + unichr(2)
    """Represents panel function key #2"""
    KEY_F3 = unichr(3) + unichr(3) + unichr(3)
    """Represents panel function key #3"""
    KEY_F4 = unichr(4) + unichr(4) + unichr(4)
    """Represents panel function key #4"""

    BATTERY_TIMEOUT = 30
    """Default timeout (in seconds) before the battery status reverts."""
    FIRE_TIMEOUT = 30
    """Default tTimeout (in seconds) before the fire status reverts."""

    # Attributes
    address = 18
    """The keypad address in use by the device."""
    configbits = 0xFF00
    """The configuration bits set on the device."""
    address_mask = 0x00000000
    """The address mask configured on the device."""
    emulate_zone = [False for _ in range(5)]
    """List containing the devices zone emulation status."""
    emulate_relay = [False for _ in range(4)]
    """List containing the devices relay emulation status."""
    emulate_lrr = False
    """The status of the devices LRR emulation."""
    deduplicate = False
    """The status of message deduplication as configured on the device."""

    def __init__(self, device):
        """
        Constructor

        :param device: The low-level device used for this `AlarmDecoder`_
                       interface.
        :type device: Device
        """
        self._device = device
        self._zonetracker = Zonetracker()

        self._battery_timeout = AlarmDecoder.BATTERY_TIMEOUT
        self._fire_timeout = AlarmDecoder.FIRE_TIMEOUT
        self._power_status = None
        self._alarm_status = None
        self._bypass_status = None
        self._armed_status = None
        self._fire_status = (False, 0)
        self._battery_status = (False, 0)
        self._panic_status = None
        self._relay_status = {}

        self.address = 18
        self.configbits = 0xFF00
        self.address_mask = 0x00000000
        self.emulate_zone = [False for x in range(5)]
        self.emulate_relay = [False for x in range(4)]
        self.emulate_lrr = False
        self.deduplicate = False

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

    def open(self, baudrate=None, no_reader_thread=False):
        """
        Opens the device.

        :param baudrate: baudrate used for the device.  Defaults to the lower-level device default.
        :type baudrate: int
        :param no_reader_thread: Specifies whether or not the automatic reader
                                 thread should be started.
        :type no_reader_thread: bool
        """
        self._wire_events()
        self._device.open(baudrate=baudrate, no_reader_thread=no_reader_thread)

        return self

    def close(self):
        """
        Closes the device.
        """
        if self._device:
            self._device.close()

        del self._device
        self._device = None

    def send(self, data):
        """
        Sends data to the `AlarmDecoder`_ device.

        :param data: data to send
        :type data: string
        """
        if self._device:
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
        config_string = ''
        config_entries = []

        # HACK: This is ugly.. but I can't think of an elegant way of doing it.
        config_entries.append(('ADDRESS',
                               '{0}'.format(self.address)))
        config_entries.append(('CONFIGBITS',
                               '{0:x}'.format(self.configbits)))
        config_entries.append(('MASK',
                               '{0:x}'.format(self.address_mask)))
        config_entries.append(('EXP',
                               ''.join(['Y' if z else 'N' for z in self.emulate_zone])))
        config_entries.append(('REL',
                               ''.join(['Y' if r else 'N' for r in self.emulate_relay])))
        config_entries.append(('LRR',
                               'Y' if self.emulate_lrr else 'N'))
        config_entries.append(('DEDUPLICATE',
                               'Y' if self.deduplicate else 'N'))

        config_string = '&'.join(['='.join(t) for t in config_entries])

        self.send("C{0}\r".format(config_string))

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

    def _handle_message(self, data):
        """
        Parses keypad messages from the panel.

        :param data: keypad data to parse
        :type data: string

        :returns: :py:class:`~alarmdecoder.messages.Message`
        """
        if data is None:
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

        elif data.startswith('!Ready'):
            self.on_boot()

        elif data.startswith('!CONFIG'):
            self._handle_config(data)

        return msg

    def _handle_keypad_message(self, data):
        """
        Handle keypad messages.

        :param data: keypad message to parse
        :type data: string

        :returns: :py:class:`~alarmdecoder.messages.Message`
        """
        msg = Message(data)

        if self.address_mask & msg.mask > 0:
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

        if msg.event_type == 'ALARM_PANIC':
            self._panic_status = True
            self.on_panic(status=True)

        elif msg.event_type == 'CANCEL':
            if self._panic_status is True:
                self._panic_status = False
                self.on_panic(status=False)

        self.on_lrr_message(message=msg)

        return msg

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
                self.emulate_zone = [val[z] == 'Y' for z in range(5)]
            elif key == 'REL':
                self.emulate_relay = [val[r] == 'Y' for r in range(4)]
            elif key == 'LRR':
                self.emulate_lrr = (val == 'Y')
            elif key == 'DEDUPLICATE':
                self.deduplicate = (val == 'Y')

        self.on_config_received()

    def _update_internal_states(self, message):
        """
        Updates internal device states.

        :param message: :py:class:`~alarmdecoder.messages.Message` to update internal states with
        :type message: :py:class:`~alarmdecoder.messages.Message`, :py:class:`~alarmdecoder.messages.ExpanderMessage`, :py:class:`~alarmdecoder.messages.LRRMessage`, or :py:class:`~alarmdecoder.messages.RFMessage`
        """
        if isinstance(message, Message):
            self._update_power_status(message)
            self._update_alarm_status(message)
            self._update_zone_bypass_status(message)
            self._update_armed_status(message)
            self._update_battery_status(message)
            self._update_fire_status(message)

        elif isinstance(message, ExpanderMessage):
            self._update_expander_status(message)

        self._update_zone_tracker(message)

    def _update_power_status(self, message):
        """
        Uses the provided message to update the AC power state.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`

        :returns: bool indicating the new status
        """
        if message.ac_power != self._power_status:
            self._power_status, old_status = message.ac_power, self._power_status

            if old_status is not None:
                self.on_power_changed(status=self._power_status)

        return self._power_status

    def _update_alarm_status(self, message):
        """
        Uses the provided message to update the alarm state.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`

        :returns: bool indicating the new status
        """

        if message.alarm_sounding != self._alarm_status:
            self._alarm_status, old_status = message.alarm_sounding, self._alarm_status

            if old_status is not None:
                self.on_alarm(status=self._alarm_status)

        return self._alarm_status

    def _update_zone_bypass_status(self, message):
        """
        Uses the provided message to update the zone bypass state.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`

        :returns: bool indicating the new status
        """

        if message.zone_bypassed != self._bypass_status:
            self._bypass_status, old_status = message.zone_bypassed, self._bypass_status

            if old_status is not None:
                self.on_bypass(status=self._bypass_status)

        return self._bypass_status

    def _update_armed_status(self, message):
        """
        Uses the provided message to update the armed state.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`

        :returns: bool indicating the new status
        """

        message_status = message.armed_away | message.armed_home
        if message_status != self._armed_status:
            self._armed_status, old_status = message_status, self._armed_status

            if old_status is not None:
                if self._armed_status:
                    self.on_arm()
                else:
                    self.on_disarm()

        return self._armed_status

    def _update_battery_status(self, message):
        """
        Uses the provided message to update the battery state.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`

        :returns: boolean indicating the new status
        """

        last_status, last_update = self._battery_status
        if message.battery_low == last_status:
            self._battery_status = (last_status, time.time())
        else:
            if message.battery_low is True or time.time() > last_update + self._battery_timeout:
                self._battery_status = (message.battery_low, time.time())
                self.on_low_battery(status=message.battery_low)

        return self._battery_status[0]

    def _update_fire_status(self, message):
        """
        Uses the provided message to update the fire alarm state.

        :param message: message to use to update
        :type message: :py:class:`~alarmdecoder.messages.Message`

        :returns: boolean indicating the new status
        """

        last_status, last_update = self._fire_status
        if message.fire_alarm == last_status:
            self._fire_status = (last_status, time.time())
        else:
            if message.fire_alarm is True or time.time() > last_update + self._fire_timeout:
                self._fire_status = (message.fire_alarm, time.time())
                self.on_fire(status=message.fire_alarm)

        return self._fire_status[0]

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
            if not message.ready and "Hit * for faults" in message.text:
                self.send('*')
                return

        self._zonetracker.update(message)

    def _on_open(self, sender, *args, **kwargs):
        """
        Internal handler for opening the device.
        """
        self.get_config()

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
