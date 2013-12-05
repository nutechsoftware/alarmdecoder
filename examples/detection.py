import time
from pyad2 import AD2
from pyad2.devices import USBDevice

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

    except Exception, ex:
        print 'Exception:', ex

    finally:
        # Close all devices and stop detection.
        for sn, device in __devices.iteritems():
            device.close()

        USBDevice.stop_detection()

def create_device(device_args):
    """
    Creates an AD2 from the specified USB device arguments.

    :param device_args: Tuple containing information on the USB device to open.
    :type device_args: Tuple (vid, pid, serialnumber, interface_count, description)
    """
    device = AD2(USBDevice.find(device_args))
    device.on_message += handle_message
    device.open()

    return device

def handle_message(sender, *args, **kwargs):
    """
    Handles message events from the AD2.
    """
    msg = kwargs['message']

    print sender, msg.raw

def handle_attached(sender, *args, **kwargs):
    """
    Handles attached events from USBDevice.start_detection().
    """
    device_args = kwargs['device']

    # Create the device from the specified device arguments.
    device = create_device(device_args)
    __devices[device.id] = device

    print 'attached', device.id

def handle_detached(sender, *args, **kwargs):
    """
    Handles detached events from USBDevice.start_detection().
    """
    device = kwargs['device']
    vendor, product, sernum, ifcount, description = device

    # Close and remove the device from our list.
    if sernum in __devices.keys():
        __devices[sernum].close()

        del __devices[sernum]

    print 'detached', sernum

if __name__ == '__main__':
    main()
