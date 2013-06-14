"""
Provides the full AD2USB class and factory.
"""

import time
import threading
import re
import logging
from .event import event
from . import devices
from . import util

class Overseer(object):
    """
    Factory for creation of AD2USB devices as well as provide4s attach/detach events."
    """

    # Factory events
    on_attached = event.Event('Called when an AD2USB device has been detected.')
    on_detached = event.Event('Called when an AD2USB device has been removed.')

    __devices = []

    @classmethod
    def find_all(cls):
        """
        Returns all AD2USB devices located on the system.
        """
        cls.__devices = devices.USBDevice.find_all()

        return cls.__devices

    @classmethod
    def devices(cls):
        """
        Returns a cached list of AD2USB devices located on the system.
        """
        return cls.__devices

    @classmethod
    def create(cls, device=None):
        """
        Factory method that returns the requested AD2USB device, or the first device.
        """
        cls.find_all()

        if len(cls.__devices) == 0:
            raise util.NoDeviceError('No AD2USB devices present.')

        if device is None:
            device = cls.__devices[0]

        vendor, product, sernum, ifcount, description = device
        device = devices.USBDevice(serial=sernum, description=description)

        return AD2USB(device)

    def __init__(self, attached_event=None, detached_event=None):
        """
        Constructor
        """
        self._detect_thread = Overseer.DetectThread(self)

        if attached_event:
            self.on_attached += attached_event

        if detached_event:
            self.on_detached += detached_event

        Overseer.find_all()

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
        """
        return Overseer.create(device)

    class DetectThread(threading.Thread):
        """
        Thread that handles detection of added/removed devices.
        """
        def __init__(self, overseer):
            """
            Constructor
            """
            threading.Thread.__init__(self)

            self._overseer = overseer
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
                    Overseer.find_all()

                    current_devices = set(Overseer.devices())
                    new_devices = [d for d in current_devices if d not in last_devices]
                    removed_devices = [d for d in last_devices if d not in current_devices]
                    last_devices = current_devices

                    for d in new_devices:
                        self._overseer.on_attached(d)

                    for d in removed_devices:
                        self._overseer.on_detached(d)

                except util.CommError, err:
                    pass

                time.sleep(0.25)


class AD2USB(object):
    """
    High-level wrapper around AD2USB/AD2SERIAL devices.
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

    # Mid-level Events
    on_message = event.Event('Called when a message has been received from the device.')

    # Low-level Events
    on_open = event.Event('Called when the device has been opened.')
    on_close = event.Event('Called when the device has been closed.')
    on_read = event.Event('Called when a line has been read from the device.')
    on_write = event.Event('Called when data has been written to the device.')

    # Constants
    F1 = unichr(1) + unichr(1) + unichr(1)
    F2 = unichr(2) + unichr(2) + unichr(2)
    F3 = unichr(3) + unichr(3) + unichr(3)
    F4 = unichr(4) + unichr(4) + unichr(4)

    def __init__(self, device):
        """
        Constructor
        """
        self._device = device
        self._power_status = None
        self._alarm_status = None
        self._bypass_status = None
        self._armed_status = None
        self._fire_status = None

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
        The ID of the AD2USB device.
        """
        return self._device.id

    def open(self, baudrate=None, interface=None, index=None, no_reader_thread=False):
        """
        Opens the device.
        """
        self._wire_events()
        self._device.open(baudrate=baudrate, interface=interface, index=index, no_reader_thread=no_reader_thread)

    def close(self):
        """
        Closes the device.
        """
        self._device.close()
        del self._device
        self._device = None

    def get_config(self):
        """
        Retrieves the configuration from the device.
        """
        self._device.write("C\r")

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

        self._device.write("C{0}\r".format(config_string))

    def reboot(self):
        """
        Reboots the device.
        """
        self._device.write('=')

    def fault_zone(self, zone, simulate_wire_problem=False):
        """
        Faults a zone if we are emulating a zone expander.
        """
        status = 2 if simulate_wire_problem else 1

        self._device.write("L{0:02}{1}\r".format(zone, status))

    def clear_zone(self, zone):
        """
        Clears a zone if we are emulating a zone expander.
        """
        self._device.write("L{0:02}0\r".format(zone))

    def _wire_events(self):
        """
        Wires up the internal device events.
        """
        self._device.on_open += self._on_open
        self._device.on_close += self._on_close
        self._device.on_read += self._on_read
        self._device.on_write += self._on_write

    def _handle_message(self, data):
        """
        Parses messages from the panel.
        """
        if data is None:
            return None

        msg = None

        if data[0] != '!':
            msg = Message(data)

            if self.address_mask & msg.mask > 0:
                self._update_internal_states(msg)

        else:   # specialty messages
            header = data[0:4]

            if header == '!EXP' or header == '!REL':
                msg = ExpanderMessage(data)
            elif header == '!RFX':
                msg = RFMessage(data)
            elif header == '!LRR':
                msg = LRRMessage(data)
            elif data.startswith('!Ready'):
                self.on_boot()
            elif data.startswith('!CONFIG'):
                self._handle_config(data)

        return msg

    def _handle_config(self, data):
        """
        Handles received configuration data.
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
                    self.emulate_zone[z] = True if v[z] == 'Y' else False
            elif k == 'REL':
                for r in range(4):
                    self.emulate_relay[r] = True if v[r] == 'Y' else False
            elif k == 'LRR':
                self.emulate_lrr = True if v == 'Y' else False
            elif k == 'DEDUPLICATE':
                self.deduplicate = True if v == 'Y' else False

        self.on_config_received()

    def _update_internal_states(self, message):
        """
        Updates internal device states.
        """
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

        if message.fire_alarm != self._fire_status:
            self._fire_status, old_status = message.fire_alarm, self._fire_status

            if old_status is not None:
                self.on_fire(self._fire_status)

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

class Message(object):
    """
    Represents a message from the alarm panel.
    """

    def __init__(self, data=None):
        """
        Constructor
        """
        self.ready = False
        self.armed_away = False
        self.armed_home = False
        self.backlight_on = False
        self.programming_mode = False
        self.beeps = -1
        self.zone_bypassed = False
        self.ac_power = False
        self.chime_on = False
        self.alarm_event_occurred = False
        self.alarm_sounding = False
        self.battery_low = False
        self.entry_delay_off = False
        self.fire_alarm = False
        self.check_zone = False
        self.perimeter_only = False
        self.numeric_code = ""
        self.text = ""
        self.cursor_location = -1
        self.data = ""
        self.mask = ""
        self.bitfield = ""
        self.panel_data = ""

        self._regex = re.compile('("(?:[^"]|"")*"|[^,]*),("(?:[^"]|"")*"|[^,]*),("(?:[^"]|"")*"|[^,]*),("(?:[^"]|"")*"|[^,]*)')

        if data is not None:
            self._parse_message(data)

    def _parse_message(self, data):
        """
        Parse the message from the device.
        """
        m = self._regex.match(data)

        if m is None:
            raise util.InvalidMessageError('Received invalid message: {0}'.format(data))

        self.bitfield, self.numeric_code, self.panel_data, alpha = m.group(1, 2, 3, 4)
        self.mask = int(self.panel_data[3:3+8], 16)

        self.data = data
        self.ready = not self.bitfield[1:2] == "0"
        self.armed_away = not self.bitfield[2:3] == "0"
        self.armed_home = not self.bitfield[3:4] == "0"
        self.backlight_on = not self.bitfield[4:5] == "0"
        self.programming_mode = not self.bitfield[5:6] == "0"
        self.beeps = int(self.bitfield[6:7], 16)
        self.zone_bypassed = not self.bitfield[7:8] == "0"
        self.ac_power = not self.bitfield[8:9] == "0"
        self.chime_on = not self.bitfield[9:10] == "0"
        self.alarm_event_occurred = not self.bitfield[10:11] == "0"
        self.alarm_sounding = not self.bitfield[11:12] == "0"
        self.battery_low = not self.bitfield[12:13] == "0"
        self.entry_delay_off = not self.bitfield[13:14] == "0"
        self.fire_alarm = not self.bitfield[14:15] == "0"
        self.check_zone = not self.bitfield[15:16] == "0"
        self.perimeter_only = not self.bitfield[16:17] == "0"
        # bits 17-20 unused.
        self.text = alpha.strip('"')

        if int(self.panel_data[19:21], 16) & 0x01 > 0:
            self.cursor_location = int(self.bitfield[21:23], 16)    # Alpha character index that the cursor is on.

    def __str__(self):
        """
        String conversion operator.
        """
        return 'msg > {0:0<9} [{1}{2}{3}] -- ({4}) {5}'.format(hex(self.mask), 1 if self.ready else 0, 1 if self.armed_away else 0, 1 if self.armed_home else 0, self.numeric_code, self.text)

class ExpanderMessage(object):
    """
    Represents a message from a zone or relay expansion module.
    """

    ZONE = 0
    RELAY = 1

    def __init__(self, data=None):
        """
        Constructor
        """
        self.type = None
        self.address = None
        self.channel = None
        self.value = None
        self.raw = None

        if data is not None:
            self._parse_message(data)

    def __str__(self):
        """
        String conversion operator.
        """
        expander_type = 'UNKWN'
        if self.type == ExpanderMessage.ZONE:
            expander_type = 'ZONE'
        elif self.type  == ExpanderMessage.RELAY:
            expander_type = 'RELAY'

        return 'exp > [{0: <5}] {1}/{2} -- {3}'.format(expander_type, self.address, self.channel, self.value)

    def _parse_message(self, data):
        """
        Parse the raw message from the device.
        """
        header, values = data.split(':')
        address, channel, value = values.split(',')

        self.raw = data
        self.address = address
        self.channel = channel
        self.value = value

        if header == '!EXP':
            self.type = ExpanderMessage.ZONE
        elif header == '!REL':
            self.type = ExpanderMessage.RELAY

class RFMessage(object):
    """
    Represents a message from an RF receiver.
    """

    def __init__(self, data=None):
        """
        Constructor
        """
        self.raw = None
        self.serial_number = None
        self.value = None

        if data is not None:
            self._parse_message(data)

    def __str__(self):
        """
        String conversion operator.
        """
        return 'rf > {0}: {1}'.format(self.serial_number, self.value)

    def _parse_message(self, data):
        """
        Parses the raw message from the device.
        """
        self.raw = data

        _, values = data.split(':')
        self.serial_number, self.value = values.split(',')

class LRRMessage(object):
    """
    Represent a message from a Long Range Radio.
    """

    def __init__(self, data=None):
        """
        Constructor
        """
        self.raw = None
        self._event_data = None
        self._partition = None
        self._event_type = None

        if data is not None:
            self._parse_message(data)

    def __str__(self):
        """
        String conversion operator.
        """
        return 'lrr > {0} @ {1} -- {2}'.format(self._event_type, self._partition, self._event_data)

    def _parse_message(self, data):
        """
        Parses the raw message from the device.
        """
        self.raw = data

        _, values = data.split(':')
        self._event_data, self._partition, self._event_type = values.split(',')
