import time
import smtplib
from email.mime.text import MIMEText
from alarmdecoder import AlarmDecoder
from alarmdecoder.devices import USBDevice

# Configuration values
SUBJECT = "AlarmDecoder - ALARM"
FROM_ADDRESS = "root@localhost"
TO_ADDRESS = "root@localhost"       # NOTE: Sending an SMS is as easy as looking
                                    # up the email address format for your provider.
SMTP_SERVER = "localhost"
SMTP_USERNAME = None
SMTP_PASSWORD = None

def main():
    """
    Example application that sends an email when an alarm event is
    detected.
    """
    try:
        # Retrieve the first USB device
        device = AlarmDecoder(USBDevice.find())

        # Set up an event handler and open the device
        device.on_alarm += handle_alarm
        with device.open():
            while True:
                time.sleep(1)

    except Exception, ex:
        print 'Exception:', ex

def handle_alarm(sender, status):
    """
    Handles alarm events from the AlarmDecoder.
    """
    text = "Alarm status: {0}".format(status)

    # Build the email message
    msg = MIMEText(text)
    msg['Subject'] = SUBJECT
    msg['From'] = FROM_ADDRESS
    msg['To'] = TO_ADDRESS

    s = smtplib.SMTP(SMTP_SERVER)

    # Authenticate if needed
    if SMTP_USERNAME is not None:
        s.login(SMTP_USERNAME, SMTP_PASSWORD)

    # Send the email
    s.sendmail(FROM_ADDRESS, TO_ADDRESS, msg.as_string())
    s.quit()

    print 'sent alarm email:', text

if __name__ == '__main__':
    main()
