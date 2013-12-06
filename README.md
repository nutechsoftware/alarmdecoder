alarmdecoder - Python library for the Alarm Decoder (AD2) device family
=======================================================================

This Python module aims to provide a consistent interface for all of the Alarm
Decoder product line, including the AD2USB, AD2SERIAL and AD2PI devices.  This
also includes devices that have been exposed via [ser2sock](http://github.com/nutechsoftware/ser2sock) and supports
encryption via SSL/TLS.

Installation
------------

alarmdecoder can be installed through pip:
    pip install alarmdecoder

or from source:
    python setup.py install

Requirements
------------
* [pyftdi](https://github.com/eblot/pyftdi) >= 0.9.0
* [pyusb](http://sourceforge.net/apps/trac/pyusb/) >= 1.0.0b1
* [pyserial](http://pyserial.sourceforge.net/) >= 2.7
* [pyopenssl](https://launchpad.net/pyopenssl)

Documentation
-------------

API documentation can be found [here](http://github.com/nutechsoftware/alarmdecoder/tree/master/docs/_build/html).

Examples
--------

Basic usage:

```python

```

Please see the [examples](http://github.com/nutechsoftware/alarmdecoder/tree/master/examples) directory for more.
