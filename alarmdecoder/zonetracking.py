"""
Provides zone tracking functionality for the `AlarmDecoder`_ (AD2) device family.

.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import re
import time

from .event import event
from .messages import ExpanderMessage


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

    def __init__(self, zone=0, name='', status=CLEAR):
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

    def __init__(self):
        """
        Constructor
        """
        self._zones = {}
        self._zones_faulted = []
        self._last_zone_fault = 0

    def update(self, message):
        """
        Update zone statuses based on the current message.

        :param message: message to use to update the zone tracking
        :type message: :py:class:`~alarmdecoder.messages.Message` or :py:class:`~alarmdecoder.messages.ExpanderMessage`
        """
        if isinstance(message, ExpanderMessage):
            if message.type == ExpanderMessage.ZONE:
                zone = self.expander_to_zone(message.address, message.channel)

                status = Zone.CLEAR
                if message.value == 1:
                    status = Zone.FAULT
                elif message.value == 2:
                    status = Zone.CHECK

                # NOTE: Expander zone faults are handled differently than
                #       regular messages.  We don't include them in
                #       self._zones_faulted because they are not reported
                #       by the panel in it's rolling list of faults.
                try:
                    self._update_zone(zone, status=status)

                except IndexError:
                    self._add_zone(zone, status=status)

        else:
            # Panel is ready, restore all zones.
            #
            # NOTE: This will need to be updated to support panels with
            #       multiple partitions.  In it's current state a ready on
            #       partition #1 will end up clearing all zones, even if they
            #       exist elsewhere and it shouldn't.
            if message.ready:
                for zone in self._zones_faulted:
                    self._update_zone(zone, Zone.CLEAR)

                self._last_zone_fault = 0

            # Process fault
            elif "FAULT" in message.text or message.check_zone:
                # Apparently this representation can be both base 10
                # or base 16, depending on where the message came
                # from.
                try:
                    zone = int(message.numeric_code)
                except ValueError:
                    zone = int(message.numeric_code, 16)

                # NOTE: Odd case for ECP failures.  Apparently they report as
                #       zone 191 (0xBF) regardless of whether or not the
                #       3-digit mode is enabled... so we have to pull it out
                #       of the alpha message.
                if zone == 191:
                    zone_regex = re.compile('^CHECK (\d+).*$')

                    match = zone_regex.match(message.text)
                    if match is None:
                        return

                    zone = match.group(1)

                # Add new zones and clear expired ones.
                if zone in self._zones_faulted:
                    self._update_zone(zone)
                    self._clear_zones(zone)

                else:
                    status = Zone.FAULT
                    if message.check_zone:
                        status = Zone.CHECK

                    self._add_zone(zone, status=status)
                    self._zones_faulted.append(zone)
                    self._zones_faulted.sort()

                # Save our spot for the next message.
                self._last_zone_fault = zone

            self._clear_expired_zones()

    def expander_to_zone(self, address, channel):
        """
        Convert an address and channel into a zone number.

        :param address: expander address
        :type address: int
        :param channel: channel
        :type channel: int

        :returns: zone number associated with an address and channel
        """

        # TODO: This is going to need to be reworked to support the larger
        #       panels without fixed addressing on the expanders.

        idx = address - 7   # Expanders start at address 7.

        return address + channel + (idx * 7) + 1

    def _clear_zones(self, zone):
        """
        Clear all expired zones from our status list.

        :param zone: current zone being processed
        :type zone: int
        """
        cleared_zones = []
        found_last_faulted = found_current = at_end = False

        # First pass: Find our start spot.
        it = iter(self._zones_faulted)
        try:
            while not found_last_faulted:
                z = it.next()

                if z == self._last_zone_fault:
                    found_last_faulted = True
                    break

        except StopIteration:
            at_end = True

        # Continue until we find our end point and add zones in
        # between to our clear list.
        try:
            while not at_end and not found_current:
                z = it.next()

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
                    z = it.next()

                    if z == zone:
                        found_current = True
                        break
                    else:
                        cleared_zones += [z]

            except StopIteration:
                pass

        # Actually remove the zones and trigger the restores.
        for z in cleared_zones:
            self._update_zone(z, Zone.CLEAR)

    def _clear_expired_zones(self):
        """
        Update zone status for all expired zones.
        """
        zones = []

        for z in self._zones.keys():
            zones += [z]

        for z in zones:
            if self._zones[z].status != Zone.CLEAR and self._zone_expired(z):
                self._update_zone(z, Zone.CLEAR)

    def _add_zone(self, zone, name='', status=Zone.CLEAR):
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
            self._zones[zone] = Zone(zone=zone, name=name, status=status)

        if status != Zone.CLEAR:
            self.on_fault(zone=zone)

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

        if status is not None:
            self._zones[zone].status = status

        self._zones[zone].timestamp = time.time()

        if status == Zone.CLEAR:
            if zone in self._zones_faulted:
                self._zones_faulted.remove(zone)

            self.on_restore(zone=zone)

    def _zone_expired(self, zone):
        """
        Determine if a zone is expired or not.

        :param zone: zone number
        :type zone: int

        :returns: whether or not the zone is expired
        """
        return time.time() > self._zones[zone].timestamp + Zonetracker.EXPIRE
