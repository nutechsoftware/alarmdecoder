.. alarmdecoder documentation master file, created by
   sphinx-quickstart on Sat Jun  8 14:38:46 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Alarm Decoder's documentation!
=========================================

.. _Alarm Decoder: http://www.alarmdecoder.com
.. _examples: http://github.com/nutechsoftware/alarmdecoder/tree/master/examples

This is the API documentation for the `Alarm Decoder`_ Python library.  It provides support for interacting with the `Alarm Decoder`_ (AD2) family of security alarm devices, including the AD2USB, AD2SERIAL and AD2PI.

The source code, requirements and examples for this project may be found `here <http://github.com/nutechsoftware/alarmdecoder>`_.

Please see the `examples`_ directory for more samples, but a basic one is included below::

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

Table of Contents:

.. toctree::
   :maxdepth: 4

   alarmdecoder


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

