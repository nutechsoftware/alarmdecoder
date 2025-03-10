.. _AlarmDecoder: http://www.alarmdecoder.com
.. _ser2sock: http://github.com/nutechsoftware/ser2sock
.. _pyftdi: https://github.com/eblot/pyftdi
.. _pyusb: http://sourceforge.net/apps/trac/pyusb
.. _pyserial: http://pyserial.sourceforge.net
.. _pyopenssl: https://launchpad.net/pyopenssl
.. _readthedocs: http://alarmdecoder.readthedocs.org
.. _examples: http://github.com/nutechsoftware/alarmdecoder/tree/master/examples

============
AlarmDecoder
============

.. image:: https://img.shields.io/pypi/v/alarmdecoder
    :target: https://pypi.org/project/alarmdecoder/
.. image:: https://img.shields.io/github/actions/workflow/status/nutechsoftware/alarmdecoder/merge.yaml?label=tests
    :target: https://github.com/nutechsoftware/alarmdecoder/actions/workflows/merge.yaml

-------
Summary
-------

This Python library aims to provide a consistent interface for the
`AlarmDecoder`_ product line. (AD2USB, AD2SERIAL and AD2PI).
This also includes devices that have been exposed via `ser2sock`_, which
supports encryption via SSL/TLS.

------------
Installation
------------

AlarmDecoder can be installed through ``pip``::

    pip install alarmdecoder

or from source::

    python setup.py install

* Note: ``python-setuptools`` is required for installation.

------------
Requirements
------------

Required:

* An `AlarmDecoder`_ device
* Python 2.7
* `pyserial`_ >= 2.7

Optional:

* `pyftdi`_ >= 0.9.0
* `pyusb`_ >= 1.0.0b1
* `pyopenssl`_

-------------
Documentation
-------------

API documentation can be found at `readthedocs`_.

--------
Examples
--------

A basic example is included below. Please see the `examples`_ directory for
more.::

    import time
    from alarmdecoder import AlarmDecoder
    from alarmdecoder.devices import SerialDevice

    def main():
        """
        Example application that prints messages from the panel to the terminal.
        """
        try:
            # Retrieve the first USB device
            device = AlarmDecoder(SerialDevice(interface='/dev/ttyUSB0'))

            # Set up an event handler and open the device
            device.on_message += handle_message
            with device.open(baudrate=115200):
                while True:
                    time.sleep(1)

        except Exception as ex:
            print ('Exception:', ex)

    def handle_message(sender, message):
        """
        Handles message events from the AlarmDecoder.
        """
        print sender, message.raw

    if __name__ == '__main__':
        main()
