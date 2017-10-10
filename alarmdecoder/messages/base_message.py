import datetime

try:
    from reprlib import repr
except ImportError:
    from repr import repr

class BaseMessage(object):
    """
    Base class for messages.
    """

    raw = None
    """The raw message text"""

    timestamp = None
    """The timestamp of the message"""

    def __init__(self, data=None):
        """
        Constructor
        """
        self.timestamp = datetime.datetime.now()
        self.raw = data

    def __str__(self):
        """
        String conversion operator.
        """
        return self.raw

    def dict(self, **kwargs):
        """
        Dictionary representation.
        """
        return dict(
            time=self.timestamp,
            mesg=self.raw,
            **kwargs
        )

    def __repr__(self):
        """
        String representation.
        """
        return repr(self.dict())
