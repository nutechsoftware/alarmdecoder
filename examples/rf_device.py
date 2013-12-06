import time
from pyad2 import AD2
from pyad2.devices import USBDevice

RF_DEVICE_SERIAL_NUMBER = '0252254'

def main():
    """
    Example application that watches for an event from a specific RF device.

    This feature allows you to watch for events from RF devices if you have
    an RF receiver.  This is useful in the case of internal sensors, which
    don't emit a FAULT if the sensor is tripped and the panel is armed STAY.
    It also will monitor sensors that aren't configured.

    NOTE: You must have an RF receiver installed and enabled in your panel
          for RFX messages to be seen.
    """
    try:
        # Retrieve the first USB device
        device = AD2(USBDevice.find())

        # Set up an event handler and open the device
        device.on_rfx_message += handle_rfx
        device.open()

        # Wait for events.
        while True:
            time.sleep(1)

    except Exception, ex:
        print 'Exception:', ex

    finally:
        device.close()

def handle_rfx(sender, *args, **kwargs):
    """
    Handles RF message events from the AD2.
    """
    msg = kwargs['message']

    # Check for our target serial number and loop
    if msg.serial_number == RF_DEVICE_SERIAL_NUMBER and msg.loop[0] == True:
        print msg.serial_number, 'triggered loop #1'

if __name__ == '__main__':
    main()
