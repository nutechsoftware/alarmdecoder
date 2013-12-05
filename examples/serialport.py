import time
from pyad2 import AD2
from pyad2.devices import SerialDevice

# Configuration values
SERIAL_DEVICE = '/dev/ttyUSB0'
BAUDRATE = 115200

def main():
    """
    Example application that opens a serial device and prints messages to the terminal.
    """
    try:
        # Retrieve the specified serial device.
        device = AD2(SerialDevice(interface=SERIAL_DEVICE))

        # Set up an event handler and open the device
        device.on_message += handle_message
        device.open(baudrate=BAUDRATE)            # Override the default SerialDevice baudrate.
        device.get_config()

        # Wait for events.
        while True:
            time.sleep(1)

    except Exception, ex:
        print 'Exception:', ex

    finally:
        device.close()

def handle_message(sender, *args, **kwargs):
    """
    Handles message events from the AD2.
    """
    msg = kwargs['message']

    print sender, msg.raw

if __name__ == '__main__':
    main()
