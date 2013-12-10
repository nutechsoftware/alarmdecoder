Alarm Decoder
==================================================================
#### Interface for the Alarm Decoder (AD2) device family ####


This Python library aims to provide a consistent interface for the entire Alarm
Decoder product line, including the AD2USB, AD2SERIAL and AD2PI devices.
This also includes devices that have been exposed via [ser2sock](http://github.com/nutechsoftware/ser2sock), which
supports encryption via SSL/TLS.

Installation
------------
alarmdecoder can be installed through pip:
    ```pip install alarmdecoder```

or from source:
    ```python setup.py install```

Requirements
------------
* [pyftdi](https://github.com/eblot/pyftdi) >= 0.9.0
* [pyusb](http://sourceforge.net/apps/trac/pyusb/) >= 1.0.0b1
* [pyserial](http://pyserial.sourceforge.net/) >= 2.7
* [pyopenssl](https://launchpad.net/pyopenssl)

Documentation
-------------
API documentation can be found [here](http://github.com/nutechsoftware/alarmdecoder/tree/master/docs/build/html).

Examples
--------
A basic example is included below.  Please see the [examples](http://github.com/nutechsoftware/alarmdecoder/tree/master/examples) directory for more.


```python
import time
from alarmdecoder import AlarmDecoder
from alarmdecoder.devices import USBDevice

def main():
    """
    Example application that prints messages from the panel to the terminal.
    """
    try:
        # Retrieve the first USB device
        device = AlarmDecoder(USBDevice.find())

        # Set up an event handler and open the device
        device.on_message += handle_message
        with device.open():
            while True:
                time.sleep(1)

    except Exception, ex:
        print 'Exception:', ex

def handle_message(sender, message):
    """
    Handles message events from the AlarmDecoder.
    """
    print sender, message.raw

if __name__ == '__main__':
    main()
```
