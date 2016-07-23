import time
from alarmdecoder import AlarmDecoder
from alarmdecoder.devices import SerialDevice

# Configuration values
TARGET_ZONE = 41
WAIT_TIME = 10

SERIAL_DEVICE = '/dev/ttyUSB0'
BAUDRATE = 115200

def main():
    """
    Example application that periodically faults a virtual zone and then
    restores it.

    This is an advanced feature that allows you to emulate a virtual zone.  When
    the AlarmDecoder is configured to emulate a zone expander we can fault and
    restore those zones programmatically at will. These events can also be seen by
    others, such as home automation platforms which allows you to connect other
    devices or services and monitor them as you would any physical zone.

    For example, you could connect a ZigBee device and receiver and fault or
    restore it's zone(s) based on the data received.

    In order for this to happen you need to perform a couple configuration steps:

    1. Enable zone expander emulation on your AlarmDecoder device by hitting '!'
       in a terminal and going through the prompts.
    2. Enable the zone expander in your panel programming.
    """
    try:
        # Retrieve the first USB device
        device = AlarmDecoder(SerialDevice(interface=SERIAL_DEVICE))

        # Set up an event handlers and open the device
        device.on_zone_fault += handle_zone_fault
        device.on_zone_restore += handle_zone_restore

        with device.open(baudrate=BAUDRATE):
            last_update = time.time()
            while True:
                if time.time() - last_update > WAIT_TIME:
                    last_update = time.time()

                    device.fault_zone(TARGET_ZONE)

                time.sleep(1)

    except Exception as ex:
        print('Exception:', ex)

def handle_zone_fault(sender, zone):
    """
    Handles zone fault messages.
    """
    print('zone faulted', zone)

    # Restore the zone
    sender.clear_zone(zone)

def handle_zone_restore(sender, zone):
    """
    Handles zone restore messages.
    """
    print('zone cleared', zone)

if __name__ == '__main__':
    main()
