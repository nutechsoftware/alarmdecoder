import time
from alarmdecoder import AlarmDecoder
from alarmdecoder.devices import USBDevice

__devices = {}

def main():
    """
    Example application that shows how to handle attach/detach events generated
    by the USB devices.

    In this case we open the device and listen for messages when it is attached.
    And when it is detached we remove it from our list of monitored devices.
    """
    try:
        # Start up the detection thread such that handle_attached and handle_detached will
        # be called when devices are attached and detached, respectively.
        USBDevice.start_detection(on_attached=handle_attached, on_detached=handle_detached)

        # Wait for events.
        while True:
            time.sleep(1)

    except Exception as ex:
        print('Exception:', ex)

    finally:
        # Close all devices and stop detection.
        for sn, device in __devices.items():
            device.close()

        USBDevice.stop_detection()

def create_device(device_args):
    """
    Creates an AlarmDecoder from the specified USB device arguments.

    :param device_args: Tuple containing information on the USB device to open.
    :type device_args: Tuple (vid, pid, serialnumber, interface_count, description)
    """
    device = AlarmDecoder(USBDevice.find(device_args))
    device.on_message += handle_message
    device.open()

    return device

def handle_message(sender, message):
    """
    Handles message events from the AlarmDecoder.
    """
    print(sender, message.raw)

def handle_attached(sender, device):
    """
    Handles attached events from USBDevice.start_detection().
    """
    # Create the device from the specified device arguments.
    dev = create_device(device)
    __devices[dev.id] = dev

    print('attached', dev.id)

def handle_detached(sender, device):
    """
    Handles detached events from USBDevice.start_detection().
    """
    vendor, product, sernum, ifcount, description = device

    # Close and remove the device from our list.
    if sernum in list(__devices.keys()):
        __devices[sernum].close()

        del __devices[sernum]

    print('detached', sernum)

if __name__ == '__main__':
    main()
