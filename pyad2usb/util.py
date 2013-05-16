import ad2usb
import time
import traceback

class NoDeviceError(Exception):
    pass

class CommError(Exception):
    pass

class TimeoutError(Exception):
    pass

class Firmware(object):
    STAGE_BOOT = 1
    STAGE_LOAD = 2
    STAGE_UPLOADING = 3
    STAGE_DONE = 4

    def __init__(self):
        pass

    def __del__(self):
        pass

    @staticmethod
    def upload(dev, filename, progress_callback=None):
        def do_upload():
            with open(filename) as f:
                for line in f:
                    line = line.rstrip()
                    if line[0] == ':':
                        dev.write(line + "\r")
                        res = dev.read_line()

                        if progress_callback is not None:
                            progress_callback(Firmware.STAGE_UPLOADING)

                        time.sleep(0.05)

        def read_until(pattern, timeout=0.0):
            start_time = time.time()
            buf = ''
            position = 0

            while True:
                try:
                    char = dev.read()

                    if char is not None and char != '':
                        if char == pattern[position]:
                            position = position + 1
                            if position == len(pattern):
                                break
                        else:
                            position = 0
                except Exception, err:
                    pass

                if timeout > 0 and time.time() - start_time > timeout:
                    raise TimeoutError('Timed out waiting for pattern: {0}'.format(pattern))

        if dev is None:
            raise NoDeviceError('No device specified for firmware upload.')

        dev.close_reader()
        time.sleep(5)

        try:
            dev.write("=\r\n")
            if progress_callback is not None:
                progress_callback(Firmware.STAGE_BOOT)
            read_until('!boot', timeout=10.0)

            dev.write("=\r\n")
            if progress_callback is not None:
                progress_callback(Firmware.STAGE_LOAD)
            read_until('!load', timeout=10.0)

            do_upload()
            if progress_callback is not None:
                progress_callback(Firmware.STAGE_DONE)

        except TimeoutError, err:
            print traceback.print_exc(err)
            pass


