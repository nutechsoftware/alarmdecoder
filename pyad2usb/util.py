import ad2usb
import time

class NoDeviceError(Exception):
    pass

class CommError(Exception):
    pass

class TimeoutError(Exception):
    pass

class Firmware(object):
    def __init__(self):
        pass

    def __del__(self):
        pass

    @staticmethod
    def upload(dev, filename):
        def do_upload():
            with open(filename) as f:
                print 'firmwaring this mofo!'
                for line in f:
                    line = line.rstrip()
                    if line[0] == ':':
                        print "> {0}".format(line)
                        dev.write(line + "\r")
                        crap = dev.read_line()
                        print "< {0}".format(crap)

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
        time.sleep(1)

        try:
            dev.write("=\r\n")
            read_until('!boot', timeout=10.0)

            dev.write("=\r\n")
            read_until('!load', timeout=10.0)

            do_upload()
        except TimeoutError, err:
            print traceback.print_exc(err)
            pass


