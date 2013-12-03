"""
Provides the full AD2 class and factory.

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import time
import threading

from .event import event
from .devices import USBDevice
from .util import CommError, NoDeviceError
from .messages import Message, ExpanderMessage, RFMessage, LRRMessage
from .zonetracking import Zonetracker

class AD2Factory(object):
    """
    Factory for creation of AD2USB devices as well as provides attach/detach events."
    """

    # Factory events
    on_attached = event.Event('Called when an AD2USB device has been detected.')
    on_detached = event.Event('Called when an AD2USB device has been removed.')

    __devices = []

    @classmethod
    def find_all(cls):
        """
        Returns all AD2USB devices located on the system.

        :returns: list of devices found
        :raises: CommError
        """
        cls.__devices = USBDevice.find_all()

        return cls.__devices

    @classmethod
    def devices(cls):
        """
        Returns a cached list of AD2USB devices located on the system.

        :returns: cached list of devices found.
        """
        return cls.__devices

    @classmethod
    def create(cls, device=None):
        """
        Factory method that returns the requested AD2USB device, or the first device.

        :param device: Tuple describing the USB device to open, as returned by find_all().
        :type device: tuple

        :returns: AD2USB object utilizing the specified device.
        :raises: NoDeviceError
        """
        cls.find_all()

        if len(cls.__devices) == 0:
            raise NoDeviceError('No AD2USB devices present.')

        if device is None:
            device = cls.__devices[0]

        vendor, product, sernum, ifcount, description = device
        device = USBDevice((sernum, ifcount - 1))

        return AD2(device)

    def __init__(self, attached_event=None, detached_event=None):
        """
        Constructor

        :param attached_event: Event to trigger when a device is attached.
        :type attached_event: function
        :param detached_event: Event to trigger when a device is detached.
        :type detached_event: function
        """
        self._detect_thread = AD2Factory.DetectThread(self)

        if attached_event:
            self.on_attached += attached_event

        if detached_event:
            self.on_detached += detached_event

        AD2Factory.find_all()

        self.start()

    def close(self):
        """
        Clean up and shut down.
        """
        self.stop()

    def start(self):
        """
        Starts the detection thread, if not already running.
        """
        if not self._detect_thread.is_alive():
            self._detect_thread.start()

    def stop(self):
        """
        Stops the detection thread.
        """
        self._detect_thread.stop()

    def get_device(self, device=None):
        """
        Factory method that returns the requested AD2USB device, or the first device.

        :param device: Tuple describing the USB device to open, as returned by find_all().
        :type device: tuple
        """
        return AD2Factory.create(device)

    class DetectThread(threading.Thread):
        """
        Thread that handles detection of added/removed devices.
        """
        def __init__(self, factory):
            """
            Constructor

            :param factory: AD2Factory object to use with the thread.
            :type factory: AD2Factory
            """
            threading.Thread.__init__(self)

            self._factory = factory
            self._running = False

        def stop(self):
            """
            Stops the thread.
            """
            self._running = False

        def run(self):
            """
            The actual detection process.
            """
            self._running = True

            last_devices = set()

            while self._running:
                try:
                    AD2Factory.find_all()

                    current_devices = set(AD2Factory.devices())
                    new_devices = [d for d in current_devices if d not in last_devices]
                    removed_devices = [d for d in last_devices if d not in current_devices]
                    last_devices = current_devices

                    for d in new_devices:
                        self._factory.on_attached(d)

                    for d in removed_devices:
                        self._factory.on_detached(d)

                except CommError, err:
                    pass

                time.sleep(0.25)


class AD2(object):
    """
    High-level wrapper around AD2 devices.
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
    F1 = unichr(1) + unichr(1) + unichr(1)
    """Represents panel function key #1"""
    F2 = unichr(2) + unichr(2) + unichr(2)
    """Represents panel function key #2"""
    F3 = unichr(3) + unichr(3) + unichr(3)
    """Represents panel function key #3"""
    F4 = unichr(4) + unichr(4) + unichr(4)
    """Represents panel function key #4"""

    BATTERY_TIMEOUT = 30
    """Timeout before the battery status reverts."""
    FIRE_TIMEOUT = 30
    """Timeout before the fire status reverts."""

    def __init__(self, device):
        """
        Constructor

        :param device: The low-level device used for this AD2 interface.
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

    @property
    def id(self):
        """
        The ID of the AD2 device.

        :returns: The identification string for the device.
        """
        return self._device.id

    def open(self, baudrate=None, no_reader_thread=False):
        """
        Opens the device.

        :param baudrate: The baudrate used for the device.
        :type baudrate: int
        :param no_reader_thread: Specifies whether or not the automatic reader thread should be started or not
        :type no_reader_thread: bool
        """
        self._wire_events()
        self._device.open(baudrate=baudrate, no_reader_thread=no_reader_thread)

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
        Sends data to the AD2 device.

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

        # HACK: Both of these methods are ugly.. but I can't think of an elegant way of doing it.

        #config_string += 'ADDRESS={0}&'.format(self.address)
        #config_string += 'CONFIGBITS={0:x}&'.format(self.configbits)
        #config_string += 'MASK={0:x}&'.format(self.address_mask)
        #config_string += 'EXP={0}&'.format(''.join(['Y' if z else 'N' for z in self.emulate_zone]))
        #config_string += 'REL={0}&'.format(''.join(['Y' if r else 'N' for r in self.emulate_relay]))
        #config_string += 'LRR={0}&'.format('Y' if self.emulate_lrr else 'N')
        #config_string += 'DEDUPLICATE={0}'.format('Y' if self.deduplicate else 'N')

        config_entries = []
        config_entries.append(('ADDRESS', '{0}'.format(self.address)))
        config_entries.append(('CONFIGBITS', '{0:x}'.format(self.configbits)))
        config_entries.append(('MASK', '{0:x}'.format(self.address_mask)))
        config_entries.append(('EXP', ''.join(['Y' if z else 'N' for z in self.emulate_zone])))
        config_entries.append(('REL', ''.join(['Y' if r else 'N' for r in self.emulate_relay])))
        config_entries.append(('LRR', 'Y' if self.emulate_lrr else 'N'))
        config_entries.append(('DEDUPLICATE', 'Y' if self.deduplicate else 'N'))

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
            zone = self._zonetracker._expander_to_zone(*zone)

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

        self.on_rfx_message(msg)

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
            self.on_panic(True)

        elif msg.event_type == 'CANCEL':
            if self._panic_status == True:
                self._panic_status = False
                self.on_panic(False)

        self.on_lrr_message(msg)

        return msg

    def _handle_config(self, data):
        """
        Handles received configuration data.

        :param data: Configuration string to parse.
        :type data: str
        """
        _, config_string = data.split('>')
        for setting in config_string.split('&'):
            k, v = setting.split('=')

            if k == 'ADDRESS':
                self.address = int(v)
            elif k == 'CONFIGBITS':
                self.configbits = int(v, 16)
            elif k == 'MASK':
                self.address_mask = int(v, 16)
            elif k == 'EXP':
                for z in range(5):
                    self.emulate_zone[z] = (v[z] == 'Y')
            elif k == 'REL':
                for r in range(4):
                    self.emulate_relay[r] = (v[r] == 'Y')
            elif k == 'LRR':
                self.emulate_lrr = (v == 'Y')
            elif k == 'DEDUPLICATE':
                self.deduplicate = (v == 'Y')

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
                    self.on_power_changed(self._power_status)

            if message.alarm_sounding != self._alarm_status:
                self._alarm_status, old_status = message.alarm_sounding, self._alarm_status

                if old_status is not None:
                    self.on_alarm(self._alarm_status)

            if message.zone_bypassed != self._bypass_status:
                self._bypass_status, old_status = message.zone_bypassed, self._bypass_status

                if old_status is not None:
                    self.on_bypass(self._bypass_status)

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
                if message.battery_low == True or time.time() > self._battery_status[1] + AD2.BATTERY_TIMEOUT:
                    self._battery_status = (message.battery_low, time.time())
                    self.on_low_battery(self._battery_status)

            if message.fire_alarm == self._fire_status[0]:
                self._fire_status = (self._fire_status[0], time.time())
            else:
                if message.fire_alarm == True or time.time() > self._fire_status[1] + AD2.FIRE_TIMEOUT:
                    self._fire_status = (message.fire_alarm, time.time())
                    self.on_fire(self._fire_status)

        elif isinstance(message, ExpanderMessage):
            if message.type == ExpanderMessage.RELAY:
                self._relay_status[(message.address, message.channel)] = message.value

                self.on_relay_changed(message)

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

    def _on_open(self, sender, args):
        """
        Internal handler for opening the device.
        """
        self.on_open(args)

    def _on_close(self, sender, args):
        """
        Internal handler for closing the device.
        """
        self.on_close(args)

    def _on_read(self, sender, args):
        """
        Internal handler for reading from the device.
        """
        self.on_read(args)

        msg = self._handle_message(args)
        if msg:
            self.on_message(msg)

    def _on_write(self, sender, args):
        """
        Internal handler for writing to the device.
        """
        self.on_write(args)

    def _on_zone_fault(self, sender, args):
        """
        Internal handler for zone faults.
        """
        self.on_zone_fault(args)

    def _on_zone_restore(self, sender, args):
        """
        Internal handler for zone restoration.
        """
        self.on_zone_restore(args)
