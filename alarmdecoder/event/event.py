# event.py (improved)
#

# Based on pyevent originally found at http://www.emptypage.jp/notes/pyevent.en.html
#
# License: https://creativecommons.org/licenses/by/2.1/jp/deed.en
#
# Changes:
#   * Added type check in fire()
#   * Removed earg from fire() and added support for args/kwargs.


class Event(object):

    def __init__(self, doc=None):
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return EventHandler(self, obj)

    def __set__(self, obj, value):
        pass


class EventHandler(object):

    def __init__(self, event, obj):

        self.event = event
        self.obj = obj

    def __iter__(self):
        return iter(self._getfunctionlist())

    def _getfunctionlist(self):

        """(internal use) """

        try:
            eventhandler = self.obj.__eventhandler__
        except AttributeError:
            eventhandler = self.obj.__eventhandler__ = {}
        return eventhandler.setdefault(self.event, [])

    def add(self, func):

        """Add new event handler function.

        Event handler function must be defined like func(sender, earg).
        You can add handler also by using '+=' operator.
        """

        self._getfunctionlist().append(func)
        return self

    def remove(self, func):

        """Remove existing event handler function.

        You can remove handler also by using '-=' operator.
        """

        self._getfunctionlist().remove(func)
        return self

    def clear(self):
        del self._getfunctionlist()[:]
        return self

    def fire(self, *args, **kwargs):

        """Fire event and call all handler functions

        You can call EventHandler object itself like e(*args, **kwargs) instead of
        e.fire(*args, **kwargs).
        """

        for func in self._getfunctionlist():
            if type(func) == EventHandler:
                func.fire(*args, **kwargs)
            else:
                func(self.obj, *args, **kwargs)

    __iadd__ = add
    __isub__ = remove
    __call__ = fire
