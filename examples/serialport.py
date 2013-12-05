import time
from pyad2 import AD2
from pyad2.devices import SerialDevice

def main():
    """
    Example application that opens a serial device and prints messages to the terminal.
    """
    try:
        # Retrieve the specified serial device.
        device = AD2(SerialDevice(interface='/dev/ttyUSB0'))

        # Set up an event handler and open the device
        device.on_message += handle_message
        device.open(baudrate=115200)            # Override the default SerialDevice baudrate.
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
