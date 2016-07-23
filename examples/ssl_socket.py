import time
from alarmdecoder import AlarmDecoder
from alarmdecoder.devices import SocketDevice

# Configuration values
HOSTNAME = 'localhost'
PORT = 10000
SSL_KEY = 'cert.key'
SSL_CERT = 'cert.pem'
SSL_CA = 'ca.pem'

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
        ssl_device.ssl_ca = SSL_CA              # CA certificate
        ssl_device.ssl_key = SSL_KEY            # Client private key
        ssl_device.ssl_certificate = SSL_CERT   # Client certificate

        device = AlarmDecoder(ssl_device)

        # Set up an event handler and open the device
        device.on_message += handle_message
        with device.open():
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
