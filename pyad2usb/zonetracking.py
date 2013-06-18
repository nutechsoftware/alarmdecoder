"""
Provides zone tracking functionality for the AD2USB device family.
"""

import time
from .event import event

class Zone(object):
    """
    Representation of a panel zone.
    """

    CLEAR = 0
    FAULT = 1
    CHECK = 2   # Wire fault

    STATUS = { CLEAR: 'CLEAR', FAULT: 'FAULT', CHECK: 'CHECK' }

    def __init__(self, zone=0, name='', status=CLEAR):
        self.zone = zone
        self.name = name
        self.status = status
        self.timestamp = time.time()

    def __str__(self):
        return 'Zone {0} {1}'.format(self.zone, self.name)

    def __repr__(self):
        return 'Zone({0}, {1}, ts {2})'.format(self.zone, Zone.STATUS[self.status], self.timestamp)

class Zonetracker(object):
    """
    Handles tracking of zone and their statuses.
    """

    on_fault = event.Event('Called when the device detects a zone fault.')
    on_restore = event.Event('Called when the device detects that a fault is restored.')

    EXPIRE = 30

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
        """
        # Panel is ready, restore all zones.
        if message.ready:
            for idx, z in enumerate(self._zones_faulted):
                self._update_zone(z, Zone.CLEAR)

            self._last_zone_fault = 0

        # Process fault
        elif "FAULT" in message.text or message.check_zone:
            zone = -1

            # Apparently this representation can be both base 10
            # or base 16, depending on where the message came
            # from.
            try:
                zone = int(message.numeric_code)
            except ValueError:
                zone = int(message.numeric_code, 16)

            # Add new zones and clear expired ones.
            if zone in self._zones_faulted:
                self._update_zone(zone)
                self._clear_zones(zone)
            else:
                status = Zone.FAULT
                if message.check_zone:
                    status = Zone.CHECK

                self._add_zone(zone, status=status)

            # Save our spot for the next message.
            self._last_zone_fault = zone

        self._clear_expired_zones()

    def _clear_zones(self, zone):
        """
        Clear all expired zones from our status list.
        """
        cleared_zones = []
        found_last = found_new = at_end = False

        #print 'zones', self._zones

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
        cleared_zones = []

        for z in self._zones_faulted:
            cleared_zones += [z]

        for z in cleared_zones:
            if self._zone_expired(z):
                self._update_zone(z, Zone.CLEAR)

    def _add_zone(self, zone, name='', status=Zone.CLEAR):
        """
        Adds a zone to the internal zone list.
        """
        if not zone in self._zones:
            self._zones[zone] = Zone(zone=zone, name=name, status=status)

        if status != Zone.CLEAR:
            self._zones_faulted.append(zone)
            self._zones_faulted.sort()
            self.on_fault(zone)

    def _update_zone(self, zone, status=None):
        """
        Updates a zones status.
        """
        if not zone in self._zones:
            raise IndexError('Zone does not exist and cannot be updated: %d', zone)

        if status is not None:
            self._zones[zone].status = status

        self._zones[zone].timestamp = time.time()

        if status == Zone.CLEAR:
            self._zones_faulted.remove(zone)
            self.on_restore(zone)

    def _zone_expired(self, zone):
        if time.time() > self._zones[zone].timestamp + Zonetracker.EXPIRE:
            return True

        return False
