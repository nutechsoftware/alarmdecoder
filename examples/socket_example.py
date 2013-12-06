import time
from pyad2 import AD2
from pyad2.devices import SocketDevice

# Configuration values
HOSTNAME = 'localhost'
PORT = 10000

def main():
    """
    Example application that opens a device that has been exposed to the network
    with ser2sock or similar serial-to-IP software.
    """
    try:
        # Retrieve an AD2 device that has been exposed with ser2sock on localhost:10000.
        device = AD2(SocketDevice(interface=(HOSTNAME, PORT)))

        # Set up an event handler and open the device
        device.on_message += handle_message
        device.open()

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
