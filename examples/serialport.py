import time
from alarmdecoder import AlarmDecoder
from alarmdecoder.devices import SerialDevice

# Configuration values
SERIAL_DEVICE = '/dev/ttyUSB0'
BAUDRATE = 115200

def main():
    """
    Example application that opens a serial device and prints messages to the terminal.
    """
    try:
        # Retrieve the specified serial device.
        device = AlarmDecoder(SerialDevice(interface=SERIAL_DEVICE))

        # Set up an event handler and open the device
        device.on_message += handle_message

        # Override the default SerialDevice baudrate since we're using a USB device
        # over serial in this example.
        with device.open(baudrate=BAUDRATE):
            while True:
                time.sleep(1)

    except Exception as ex:
        print('Exception:', ex)

def handle_message(sender, message):
    """
    Handles message events from the AlarmDecoder.
    """
    print(sender, message.raw)

if __name__ == '__main__':
    main()
