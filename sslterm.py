#!/usr/bin/env python

import pyad2usb.ad2usb
import sys, select
import termios, tty
import time

def main():
    def handle_open(sender, args):
        print "Connection open.\r"

    def handle_close(sender, args):
        print "Connection closed.\r"

    def handle_read(sender, args):
        print '<', args, "\r"

    if len(sys.argv) != 5:
        print "Syntax: sslterm.py [host:port] [ca cert] [client cert] [client key]\r"
        return 1

    host, port = sys.argv[1].split(':')
    ca_cert = sys.argv[2]
    client_cert = sys.argv[3]
    client_key = sys.argv[4]

    running = True

    old_term_settings = termios.tcgetattr(sys.stdin.fileno())
    tty.setraw(sys.stdin.fileno())

    try:
        dev = pyad2usb.ad2usb.devices.SocketDevice(interface=(host, int(port)), use_ssl=True, ssl_certificate=client_cert, ssl_key=client_key, ssl_ca=ca_cert)

        a2u = pyad2usb.ad2usb.AD2USB(dev)
        a2u.on_open += handle_open
        a2u.on_close += handle_close
        a2u.on_read += handle_read

        a2u.open()
        #dev.open(no_reader_thread=True)

        while running:
            data = None

            ifh, ofh, efh = select.select([sys.stdin], [], [], 0)
            if ifh:
                data = sys.stdin.read(1)

                if data:
                    if data == "\x03":
                        print "Exiting..\r"
                        running = False
                        break

                    else:
                        a2u.send(data)

        a2u.close()

            #ifh, ofh, efh = select.select([sys.stdin, dev._device], [], [], 0)
            #for h in ifh:
            #    data = h.read(1)
            #
            #    if h == sys.stdin:
            #        if data == "\x03":
            #            print "Exiting..\r"
            #            running = False
            #            break
            #
            #        else:
            #            dev.write(data)
            #
            #    else:
            #        sys.stdout.write(data)
            #        sys.stdout.flush()

        #dev.close()

    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_term_settings)


if __name__ == '__main__':
    main()
