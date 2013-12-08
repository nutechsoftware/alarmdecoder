"""
Provides the full AlarmDecoder class.

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import time

from .event import event
from .util import InvalidMessageError
from .messages import Message, ExpanderMessage, RFMessage, LRRMessage
from .zonetracking import Zonetracker


class AlarmDecoder(object):
    """
    High-level wrapper around Alarm Decoder (AD2) devices.
    """

    # High-level Events
    on_arm = event.Event('Called when the panel is armed.')
    on_disarm = event.Event('Called when the panel is disarmed.')
    on_power_changed = event.Event('Called when panel power switches between AC and DC.')
    on_alarm = event.Event('Called when the alarm is triggered.')
    on_fire = event.Event('Called when a fire is detected.')
    on_bypass = event.Event('Called when a zone is bypassed.')
    on_boot = event.Event('Called when the device finishes bootings.')
    on_config_received = event.Event('Called when the device receives its configuration.')
    on_zone_fault = event.Event('Called when the device detects a zone fault.')
    on_zone_restore = event.Event('Called when the device detects that a fault is restored.')
    on_low_battery = event.Event('Called when the device detects a low battery.')
    on_panic = event.Event('Called when the device detects a panic.')
    on_relay_changed = event.Event('Called when a relay is opened or closed on an expander board.')

    # Mid-level Events
    on_message = event.Event('Called when a message has been received from the device.')
    on_lrr_message = event.Event('Called when an LRR message is received.')
    on_rfx_message = event.Event('Called when an RFX message is received.')

    # Low-level Events
    on_open = event.Event('Called when the device has been opened.')
    on_close = event.Event('Called when the device has been closed.')
    on_read = event.Event('Called when a line has been read from the device.')
    on_write = event.Event('Called when data has been written to the device.')

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
    """Timeout before the battery status reverts."""
    FIRE_TIMEOUT = 30
    """Timeout before the fire status reverts."""

    def __init__(self, device):
        """
        Constructor

        :param device: The low-level device used for this Alarm Decoder
                       interface.
        :type device: Device
        """
        self._device = device
        self._zonetracker = Zonetracker()

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
        The ID of the Alarm Decoder device.

        :returns: The identification string for the device.
        """
        return self._device.id

    def open(self, baudrate=None, no_reader_thread=False):
        """
        Opens the device.

        :param baudrate: The baudrate used for the device.
        :type baudrate: int
        :param no_reader_thread: Specifies whether or not the automatic reader
                                 thread should be started or not
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
        Sends data to the Alarm Decoder device.

        :param data: The data to send.
        :type data: str
        """
        if self._device:
            self._device.write(data)

    def get_config(self):
        """
        Retrieves the configuration from the device.
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

        :param zone: The zone to fault.
        :type zone: int
        :param simulate_wire_problem: Whether or not to simulate a wire fault.
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

        :param zone: The zone to clear.
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
        Parses messages from the panel.

        :param data: Panel data to parse.
        :type data: str

        :returns: An object representing the message.
        """
        if data is None:
            raise InvalidMessageError()

        msg = None
        header = data[0:4]

        if header[0] != '!' or header == '!KPE':
            msg = Message(data)

            if self.address_mask & msg.mask > 0:
                self._update_internal_states(msg)

        elif header == '!EXP' or header == '!REL':
            msg = ExpanderMessage(data)

            self._update_internal_states(msg)

        elif header == '!RFX':
            msg = self._handle_rfx(data)

        elif header == '!LRR':
            msg = self._handle_lrr(data)

        elif data.startswith('!Ready'):
            self.on_boot()

        elif data.startswith('!CONFIG'):
            self._handle_config(data)

        return msg

    def _handle_rfx(self, data):
        """
        Handle RF messages.

        :param data: RF message to parse.
        :type data: str

        :returns: An object representing the RF message.
        """
        msg = RFMessage(data)

        self.on_rfx_message(message=msg)

        return msg

    def _handle_lrr(self, data):
        """
        Handle Long Range Radio messages.

        :param data: LRR message to parse.
        :type data: str

        :returns: An object representing the LRR message.
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

        :param data: Configuration string to parse.
        :type data: str
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

        :param message: Message to update internal states with.
        :type message: Message, ExpanderMessage, LRRMessage, or RFMessage
        """
        if isinstance(message, Message):
            if message.ac_power != self._power_status:
                self._power_status, old_status = message.ac_power, self._power_status

                if old_status is not None:
                    self.on_power_changed(status=self._power_status)

            if message.alarm_sounding != self._alarm_status:
                self._alarm_status, old_status = message.alarm_sounding, self._alarm_status

                if old_status is not None:
                    self.on_alarm(status=self._alarm_status)

            if message.zone_bypassed != self._bypass_status:
                self._bypass_status, old_status = message.zone_bypassed, self._bypass_status

                if old_status is not None:
                    self.on_bypass(status=self._bypass_status)

            if (message.armed_away | message.armed_home) != self._armed_status:
                self._armed_status, old_status = message.armed_away | message.armed_home, self._armed_status

                if old_status is not None:
                    if self._armed_status:
                        self.on_arm()
                    else:
                        self.on_disarm()

            if message.battery_low == self._battery_status[0]:
                self._battery_status = (self._battery_status[0], time.time())
            else:
                if message.battery_low is True or time.time() > self._battery_status[1] + AlarmDecoder.BATTERY_TIMEOUT:
                    self._battery_status = (message.battery_low, time.time())
                    self.on_low_battery(status=self._battery_status)

            if message.fire_alarm == self._fire_status[0]:
                self._fire_status = (self._fire_status[0], time.time())
            else:
                if message.fire_alarm is True or time.time() > self._fire_status[1] + AlarmDecoder.FIRE_TIMEOUT:
                    self._fire_status = (message.fire_alarm, time.time())
                    self.on_fire(status=self._fire_status)

        elif isinstance(message, ExpanderMessage):
            if message.type == ExpanderMessage.RELAY:
                self._relay_status[(message.address, message.channel)] = message.value

                self.on_relay_changed(message=message)

        self._update_zone_tracker(message)

    def _update_zone_tracker(self, message):
        """
        Trigger an update of the zonetracker.

        :param message: The message to update the zonetracker with.
        :type message: Message, ExpanderMessage, LRRMessage, or RFMessage
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

        self.on_open(args, kwargs)

    def _on_close(self, sender, *args, **kwargs):
        """
        Internal handler for closing the device.
        """
        self.on_close(args, kwargs)

    def _on_read(self, sender, *args, **kwargs):
        """
        Internal handler for reading from the device.
        """
        self.on_read(args, kwargs)

        msg = self._handle_message(kwargs.get('data', None))
        if msg:
            self.on_message(message=msg)

    def _on_write(self, sender, *args, **kwargs):
        """
        Internal handler for writing to the device.
        """
        self.on_write(args, kwargs)

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
