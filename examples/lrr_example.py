import time
from alarmdecoder import AlarmDecoder
from alarmdecoder.devices import SerialDevice

SERIAL_DEVICE = '/dev/ttyUSB0'
BAUDRATE = 115200

def main():
    """
    Example application that prints messages from the panel to the terminal.
    """
    try:
        # Retrieve the first USB device
        device = AlarmDecoder(SerialDevice(interface=SERIAL_DEVICE))

        # Set up an event handler and open the device
        device.on_lrr_message += handle_lrr_message
        with device.open(baudrate=BAUDRATE):
            while True:
                time.sleep(1)

    except Exception as ex:
        print('Exception:', ex)

def handle_lrr_message(sender, message):
    """
    Handles message events from the AlarmDecoder.
    """
    print(sender, message.partition, message.event_type, message.event_data)

if __name__ == '__main__':
    main()
