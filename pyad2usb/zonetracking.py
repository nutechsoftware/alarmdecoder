"""
Provides zone tracking functionality for the AD2USB device family.
"""

import re
import time
from .event import event
from . import messages

class Zone(object):
    """
    Representation of a panel zone.
    """

    CLEAR = 0
    """Status indicating that the zone is cleared."""
    FAULT = 1
    """Status indicating that the zone is faulted."""
    CHECK = 2   # Wire fault
    """Status indicating that there is a wiring issue with the zone."""

    STATUS = { CLEAR: 'CLEAR', FAULT: 'FAULT', CHECK: 'CHECK' }

    def __init__(self, zone=0, name='', status=CLEAR):
        """
        Constructor

        :param zone: The zone number.
        :type zone: int
        :param name: Human readable zone name.
        :type name: str
        :param status: Initial zone state.
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
    Handles tracking of zone and their statuses.
    """

    on_fault = event.Event('Called when the device detects a zone fault.')
    on_restore = event.Event('Called when the device detects that a fault is restored.')

    EXPIRE = 30
    """Zone expiration timeout."""

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

        :param message: Message to use to update the zone tracking.
        :type message: Message or ExpanderMessage
        """
        zone = -1

        if isinstance(message, messages.ExpanderMessage):
            if message.type == messages.ExpanderMessage.ZONE:
                zone = self._expander_to_zone(int(message.address), int(message.channel))

                status = Zone.CLEAR
                if int(message.value) == 1:
                    status = Zone.FAULT
                elif int(message.value) == 2:
                    status = Zone.CHECK

                try:
                    self._update_zone(zone, status=status)
                except IndexError:
                    self._add_zone(zone, status=status)

        else:
            # Panel is ready, restore all zones.
            if message.ready:
                for idx, z in enumerate(self._zones_faulted):
                    self._update_zone(z, Zone.CLEAR)

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

                # NOTE: Odd case for ECP failures.  Apparently they report as zone 191 (0xBF) regardless
                # of whether or not the 3-digit mode is enabled... so we have to pull it out of the
                # alpha message.
                if zone == 191:
                    # TODO: parse message text.
                    zone_regex = re.compile('^CHECK (\d+).*$')

                    m = zone_regex.match(message.text)
                    if m is None:
                        return

                    zone = m.group(1)

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

    def _clear_zones(self, zone):
        """
        Clear all expired zones from our status list.

        :param zone: current zone being processed.
        :type zone: int
        """
        cleared_zones = []
        found_last = found_new = at_end = False

        # First pass: Find our start spot.
        it = iter(self._zones_faulted)
        try:
            while not found_last:
                z = it.next()

                if z == self._last_zone_fault:
                    found_last = True
                    break

        except StopIteration:
            at_end = True

        # Continue until we find our end point and add zones in
        # between to our clear list.
        try:
            while not at_end and not found_new:
                z = it.next()

                if z == zone:
                    found_new = True
                    break
                else:
                    cleared_zones += [z]

        except StopIteration:
            pass

        # Second pass: roll through the list again if we didn't find
        # our end point and remove everything until we do.
        if not found_new:
            it = iter(self._zones_faulted)

            try:
                while not found_new:
                    z = it.next()

                    if z == zone:
                        found_new = True
                        break
                    else:
                        cleared_zones += [z]

            except StopIteration:
                pass

        # Actually remove the zones and trigger the restores.
        for idx, z in enumerate(cleared_zones):
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

        :param zone: The zone number.
        :type zone: int
        :param name: Human readable zone name.
        :type name: str
        :param status: The zone status.
        :type status: int
        """
        if not zone in self._zones:
            self._zones[zone] = Zone(zone=zone, name=name, status=status)

        if status != Zone.CLEAR:
            self.on_fault(zone)

    def _update_zone(self, zone, status=None):
        """
        Updates a zones status.

        :param zone: The zone number.
        :type zone: int
        :param status: The zone status.
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

            self.on_restore(zone)

    def _zone_expired(self, zone):
        """
        Determine if a zone is expired or not.

        :param zone: The zone number.
        :type zone: int

        :returns: Whether or not the zone is expired.
        """
        if time.time() > self._zones[zone].timestamp + Zonetracker.EXPIRE:
            return True

        return False

    def _expander_to_zone(self, address, channel):
        """
        Convert an address and channel into a zone number.

        :param address: The expander address
        :type address: int
        :param channel: The channel
        :type channel: int

        :returns: The zone number associated with an address and channel.
        """

        # TODO: This is going to need to be reworked to support the larger
        #       panels without fixed addressing on the expanders.

        idx = address - 7   # Expanders start at address 7.

        return address + channel + (idx * 7) + 1
