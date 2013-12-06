import time
from pyad2 import AD2
from pyad2.devices import USBDevice

# Configuration values
TARGET_ZONE = 41
WAIT_TIME = 10

def main():
    """
    Example application that periodically faults a virtual zone and then
    restores it.

    This is an advanced feature that allows you to emulate a virtual zone.  When
    the AD2 is configured to emulate a relay expander we can fault and restore
    those zones programmatically at will. These events can also be seen by others,
    such as home automation platforms which allows you to connect other devices or
    services and monitor them as you would any pyhysical zone.

    For example, you could connect a ZigBee device and receiver and fault or
    restore it's zone(s) based on the data received.

    In order for this to happen you need to perform a couple configuration steps:

    1. Enable zone expander emulation on your AD2 device by hitting '!' in a
       terminal and going through the prompts.
    2. Enable the zone expander in your panel programming.
    """
    try:
        # Retrieve the first USB device
        device = AD2(USBDevice.find())

        # Set up an event handlers and open the device
        device.on_zone_fault += handle_zone_fault
        device.on_zone_restore += handle_zone_restore

        device.open()

        # Wait for events.
        last_update = time.time()
        while True:
            if time.time() - last_update > WAIT_TIME:
                last_update = time.time()

                device.fault_zone(TARGET_ZONE)

            time.sleep(1)

    except Exception, ex:
        print 'Exception:', ex

    finally:
        device.close()

def handle_zone_fault(sender, *args, **kwargs):
    """
    Handles zone fault messages.
    """
    zone = kwargs['zone']

    print 'zone faulted', zone

    # Restore the zone
    sender.clear_zone(zone)

def handle_zone_restore(sender, *args, **kwargs):
    """
    Handles zone restore messages.
    """
    zone = kwargs['zone']

    print 'zone cleared', zone

if __name__ == '__main__':
    main()
