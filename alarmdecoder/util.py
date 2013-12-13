"""
Provides utility classes for the `AlarmDecoder`_ (AD2) devices.

.. _AlarmDecoder: http://www.alarmdecoder.com

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

import time
import threading


class NoDeviceError(Exception):
    """
    No devices found.
    """
    pass


class CommError(Exception):
    """
    There was an error communicating with the device.
    """
    pass


class TimeoutError(Exception):
    """
    There was a timeout while trying to communicate with the device.
    """
    pass


class InvalidMessageError(Exception):
    """
    The format of the panel message was invalid.
    """
    pass


class Firmware(object):
    """
    Represents firmware for the `AlarmDecoder`_ devices.
    """

    # Constants
    STAGE_START = 0
    STAGE_WAITING = 1
    STAGE_BOOT = 2
    STAGE_LOAD = 3
    STAGE_UPLOADING = 4
    STAGE_DONE = 5

    # FIXME: Rewrite this monstrosity.
    @staticmethod
    def upload(dev, filename, progress_callback=None):
        """
        Uploads firmware to an `AlarmDecoder`_ device.

        :param filename: firmware filename
        :type filename: string
        :param progress_callback: callback function used to report progress
        :type progress_callback: function

        :raises: :py:class:`~alarmdecoder.util.NoDeviceError`, :py:class:`~alarmdecoder.util.TimeoutError`
        """

        def do_upload():
            """
            Perform the actual firmware upload to the device.
            """
            with open(filename) as upload_file:
                for line in upload_file:
                    line = line.rstrip()

                    if line[0] == ':':
                        dev.write(line + "\r")
                        dev.read_line(timeout=10.0)

                        if progress_callback is not None:
                            progress_callback(Firmware.STAGE_UPLOADING)

                        time.sleep(0.0)

        def read_until(pattern, timeout=0.0):
            """
            Read characters until a specific pattern is found or the timeout is
            hit.
            """
            def timeout_event():
                """Handles the read timeout event."""
                timeout_event.reading = False

            timeout_event.reading = True

            timer = None
            if timeout > 0:
                timer = threading.Timer(timeout, timeout_event)
                timer.start()

            position = 0

            while timeout_event.reading:
                try:
                    char = dev.read()

                    if char is not None and char != '':
                        if char == pattern[position]:
                            position = position + 1
                            if position == len(pattern):
                                break
                        else:
                            position = 0

                except Exception:
                    pass

            if timer:
                if timer.is_alive():
                    timer.cancel()
                else:
                    raise TimeoutError('Timeout while waiting for line terminator.')

        def stage_callback(stage):
            """Callback to update progress for the specified stage."""
            if progress_callback is not None:
                progress_callback(stage)

        if dev is None:
            raise NoDeviceError('No device specified for firmware upload.')

        stage_callback(Firmware.STAGE_START)

        if dev.is_reader_alive():
            # Close the reader thread and wait for it to die, otherwise
            # it interferes with our reading.
            dev.stop_reader()
            while dev._read_thread.is_alive():
                stage_callback(Firmware.STAGE_WAITING)
                time.sleep(1)

        time.sleep(2)

        # Reboot the device and wait for the boot loader.
        stage_callback(Firmware.STAGE_BOOT)
        dev.write("=")
        read_until('......', timeout=15.0)

        # Get ourselves into the boot loader and wait for indication
        # that it's ready for the firmware upload.
        stage_callback(Firmware.STAGE_LOAD)
        dev.write("=")
        read_until('!load', timeout=15.0)

        # And finally do the upload.
        do_upload()
        stage_callback(Firmware.STAGE_DONE)
