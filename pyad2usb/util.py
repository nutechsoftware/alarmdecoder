import ad2usb
import time

class NoDeviceError(Exception):
    pass

class CommError(Exception):
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

		def read_until(data):
			buf = ''
			position = 0

			while True:
				try:
					char = dev.read()

					if char is not None and char != '':
						if char == data[position]:
							position = position + 1
							if position == len(data):
								return True
						else:
							position = 0
				except Exception, err:
					pass

		if dev is None:
			raise NoDeviceError('No device specified for firmware upload.')

		dev.close_reader()

		time.sleep(1)

		dev.write("=\r\n")
		read_until('!boot')

		dev.write("=\r\n")
		read_until('!load')

		do_upload()
