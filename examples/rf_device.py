import time
from alarmdecoder import AlarmDecoder
from alarmdecoder.devices import SerialDevice

RF_DEVICE_SERIAL_NUMBER = '0252254'

SERIAL_DEVICE = '/dev/ttyUSB0'
BAUDRATE = 115200

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
        device = AlarmDecoder(SerialDevice(interface=SERIAL_DEVICE))

        # Set up an event handler and open the device
        device.on_rfx_message += handle_rfx
        with device.open(baudrate=BAUDRATE):
            while True:
                time.sleep(1)

    except Exception as ex:
        print('Exception:', ex)

def handle_rfx(sender, message):
    """
    Handles RF message events from the AlarmDecoder.
    """
    # Check for our target serial number and loop
    if message.serial_number == RF_DEVICE_SERIAL_NUMBER and message.loop[0] == True:
        print(message.serial_number, 'triggered loop #1')

if __name__ == '__main__':
    main()
