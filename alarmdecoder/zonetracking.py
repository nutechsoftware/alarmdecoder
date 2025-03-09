"""
Provides zone tracking functionality for the `AlarmDecoder`_ (AD2) device family.

.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import re
import time

from .event import event
from .messages import ExpanderMessage
from .panels import ADEMCO, DSC


class Zone(object):
    """
    Representation of a panel zone.
    """

    # Constants
    CLEAR = 0
    """Status indicating that the zone is cleared."""
    FAULT = 1
    """Status indicating that the zone is faulted."""
    CHECK = 2   # Wire fault
    """Status indicating that there is a wiring issue with the zone."""

    STATUS = {CLEAR: 'CLEAR', FAULT: 'FAULT', CHECK: 'CHECK'}

    # Attributes
    zone = 0
    """Zone ID"""
    name = ''
    """Zone name"""
    status = CLEAR
    """Zone status"""
    timestamp = None
    """Timestamp of last update"""
    expander = False
    """Does this zone exist on an expander?"""

    def __init__(self, zone=0, name='', status=CLEAR, expander=False):
        """
        Constructor

        :param zone: zone number
        :type zone: int
        :param name: Human readable zone name
        :type name: string
        :param status: Initial zone state
        :type status: int
        """
        self.zone = zone
        self.name = name
        self.status = status
        self.timestamp = time.time()
        self.expander = expander

    def __str__(self):
        """
        String conversion operator.
        """
        return 'Zone {0} {1}'.format(self.zone, self.name)

    def __repr__(self):
        """
        Human readable representation operator.
        """
        return 'Zone({0}, {1}, ts {2})'.format(self.zone, Zone.STATUS[self.status], self.timestamp)


class Zonetracker(object):
    """
    Handles tracking of zones and their statuses.
    """

    on_fault = event.Event("This event is called when the device detects a zone fault.\n\n**Callback definition:** *def callback(device, zone)*")
    on_restore = event.Event("This event is called when the device detects that a fault is restored.\n\n**Callback definition:** *def callback(device, zone)*")

    EXPIRE = 30
    """Zone expiration timeout."""

    @property
    def zones(self):
        """
        Returns the current list of zones being tracked.

        :returns: dictionary of :py:class:`Zone` being tracked
        """
        return self._zones

    @zones.setter
    def zones(self, value):
        """
        Sets the current list of zones being tracked.

        :param value: new list of zones being tracked
        :type value: dictionary of :py:class:`Zone` being tracked
        """
        self._zones = value

    @property
    def faulted(self):
        """
        Retrieves the current list of faulted zones.

        :returns: list of faulted zones
        """
        return self._zones_faulted

    @faulted.setter
    def faulted(self, value):
        """
        Sets the current list of faulted zones.

        :param value: new list of faulted zones
        :type value: list of integers
        """
        self._zones_faulted = value

    def __init__(self, alarmdecoder_object):
        """
        Constructor
        """
        self._zones = {}
        self._zones_faulted = []
        self._last_zone_fault = 0

        self.alarmdecoder_object = alarmdecoder_object

    def update(self, message):
        """
        Update zone statuses based on the current message.

        :param message: message to use to update the zone tracking
        :type message: :py:class:`~alarmdecoder.messages.Message` or :py:class:`~alarmdecoder.messages.ExpanderMessage`
        """
        if isinstance(message, ExpanderMessage):
            zone = -1

            if message.type == ExpanderMessage.ZONE:
                zone = self.expander_to_zone(message.address, message.channel, self.alarmdecoder_object.mode)

            if zone != -1:
                status = Zone.CLEAR
                if message.value == 1:
                    status = Zone.FAULT
                elif message.value == 2:
                    status = Zone.CHECK

                # NOTE: Expander zone faults are handled differently than
                #       regular messages.
                try:
                    self._update_zone(zone, status=status)
                    self.zones[zone].expander = True

                except IndexError:
                    self._add_zone(zone, status=status, expander=True)

        else:
            # Panel is ready, restore all zones.
            #
            # NOTE: This will need to be updated to support panels with
            #       multiple partitions.  In it's current state a ready on
            #       partition #1 will end up clearing all zones, even if they
            #       exist elsewhere and it shouldn't.
            #
            # NOTE: SYSTEM messages provide inconsistent ready statuses.  This
            #       may need to be extended later for other panels.
            if message.ready and not message.text.startswith("SYSTEM"):
                for zone in self._zones_faulted[:]:
                    self._update_zone(zone, Zone.CLEAR)

                self._last_zone_fault = 0

            # Process fault
            elif self.alarmdecoder_object.mode != DSC and (message.check_zone or message.text.startswith("FAULT") or message.text.startswith("ALARM")):
                zone = message.parse_numeric_code()

                # NOTE: Odd case for ECP failures.  Apparently they report as
                #       zone 191 (0xBF) regardless of whether or not the
                #       3-digit mode is enabled... so we have to pull it out
                #       of the alpha message.
                if zone == 191:
                    zone_regex = re.compile(r'^CHECK (\d+).*$')

                    match = zone_regex.match(message.text)
                    if match is None:
                        return

                    zone = int(match.group(1))

                # Add new zones and clear expired ones.
                if zone in self._zones_faulted:
                    self._update_zone(zone)
                    self._clear_zones(zone)

                    # Save our spot for the next message.
                    self._last_zone_fault = zone

                else:
                    status = Zone.FAULT
                    if message.check_zone:
                        status = Zone.CHECK

                    self._add_zone(zone, status=status)
                    self._zones_faulted.append(zone)
                    self._zones_faulted.sort()

                    # A new zone fault, so it is out of sequence.
                    self._last_zone_fault = 0

            self._clear_expired_zones()

    def expander_to_zone(self, address, channel, panel_type=ADEMCO):
        """
        Convert an address and channel into a zone number.

        :param address: expander address
        :type address: int
        :param channel: channel
        :type channel: int

        :returns: zone number associated with an address and channel
        """

        zone = -1

        if panel_type == ADEMCO:
            # TODO: This is going to need to be reworked to support the larger
            #       panels without fixed addressing on the expanders.

            idx = address - 7   # Expanders start at address 7.
            zone = address + channel + (idx * 7) + 1

        elif panel_type == DSC:
            zone = (address * 8) + channel

        return zone

    def _clear_zones(self, zone):
        """
        Clear all expired zones from our status list.

        :param zone: current zone being processed
        :type zone: int
        """

        if self._last_zone_fault == 0:
            # We don't know what the last faulted zone was, nothing to do
            return

        cleared_zones = []
        found_last_faulted = found_current = at_end = False

        # First pass: Find our start spot.
        it = iter(self._zones_faulted)
        try:
            while not found_last_faulted:
                z = next(it)

                if z == self._last_zone_fault:
                    found_last_faulted = True
                    break

        except StopIteration:
            at_end = True

        # Continue until we find our end point and add zones in
        # between to our clear list.
        try:
            while not at_end and not found_current:
                z = next(it)

                if z == zone:
                    found_current = True
                    break
                else:
                    cleared_zones += [z]

        except StopIteration:
            pass

        # Second pass: roll through the list again if we didn't find
        # our end point and remove everything until we do.
        if not found_current:
            it = iter(self._zones_faulted)

            try:
                while not found_current:
                    z = next(it)

                    if z == zone:
                        found_current = True
                        break
                    else:
                        cleared_zones += [z]

            except StopIteration:
                pass

        # Actually remove the zones and trigger the restores.
        for z in cleared_zones:
            # Don't clear expander zones, expander messages will fix this
            if self._zones[z].expander is False:
                self._update_zone(z, Zone.CLEAR)

    def _clear_expired_zones(self):
        """
        Update zone status for all expired zones.
        """
        zones = []

        for z in list(self._zones.keys()):
            zones += [z]

        for z in zones:
            if self._zones[z].status != Zone.CLEAR and self._zone_expired(z):
                self._update_zone(z, Zone.CLEAR)

    def _add_zone(self, zone, name='', status=Zone.CLEAR, expander=False):
        """
        Adds a zone to the internal zone list.

        :param zone: zone number
        :type zone: int
        :param name: human readable zone name
        :type name: string
        :param status: zone status
        :type status: int
        """
        if not zone in self._zones:
            self._zones[zone] = Zone(zone=zone, name=name, status=None, expander=expander)

        self._update_zone(zone, status=status)

    def _update_zone(self, zone, status=None):
        """
        Updates a zones status.

        :param zone: zone number
        :type zone: int
        :param status: zone status
        :type status: int

        :raises: IndexError
        """
        if not zone in self._zones:
            raise IndexError('Zone does not exist and cannot be updated: %d', zone)

        old_status = self._zones[zone].status
        if status is None:
            status = old_status

        self._zones[zone].status = status
        self._zones[zone].timestamp = time.time()

        if status == Zone.CLEAR:
            if zone in self._zones_faulted:
                self._zones_faulted.remove(zone)

            self.on_restore(zone=zone)
        else:
            if old_status != status and status is not None:
                self.on_fault(zone=zone)

    def _zone_expired(self, zone):
        """
        Determine if a zone is expired or not.

        :param zone: zone number
        :type zone: int

        :returns: whether or not the zone is expired
        """
        return (time.time() > self._zones[zone].timestamp + Zonetracker.EXPIRE) and self._zones[zone].expander is False
