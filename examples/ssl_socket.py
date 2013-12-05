import time
from pyad2 import AD2
from pyad2.devices import SocketDevice

def main():
    """
    Example application that opens a device that has been exposed to the network
    with ser2sock and SSL encryption and authentication.
    """
    try:
        # Retrieve an AD2 device that has been exposed with ser2sock on localhost:10000.
        ssl_device = SocketDevice(interface=('localhost', 10000))

        # Enable SSL and set the certificates to be used.
        #
        # The key/cert attributes can either be a filesystem path or an X509/PKey
        # object from pyopenssl.
        ssl_device.ssl = True
        ssl_device.ssl_key = 'cert.key'         # Client private key
        ssl_device.ssl_certificate = 'cert.pem' # Client certificate
        ssl_device.ssl_ca = 'ca.pem'            # CA certificate

        device = AD2(ssl_device)

        # Set up an event handler and open the device
        device.on_message += handle_message
        device.open()

        time.sleep(1)          # Allow time for SSL handshake to complete.
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
