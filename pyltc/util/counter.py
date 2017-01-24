"""
Counter utility objects module.

"""
import collections


class Counter(object):

    @classmethod
    def _arg2skipset(cls, arg):
        """Converts given ``arg`` into a set if args is acceptable as a ``skip`` argument for
           ``Counter.skip(arg)`` argument or for the ``Counter(skip=arg)`` keyword argument."""
        if isinstance(arg, int):
            arg = (arg,)
        if not cls._isproperskipsequence(arg):
            raise TypeError("expected int or sequence but got {}".format(type(arg).__name__))
        return set(arg)

    @staticmethod
    def _isproperskipsequence(sequence):
        """Returns True if given ``sequence`` is acceptable as a ``Counter.skip(arg)`` argument
           or for the ``Counter(skip=arg)`` keyword argument, False otherwise."""
        if isinstance(sequence, (str, bytes)):
            return False
        if isinstance(sequence, set):
            return True
        return isinstance(sequence, collections.Sequence)

    def __init__(self, start=0, incr=1, end=None, fmt=None, skip=None):
        """
        Initializer.

        :param start: int - the start value of this counter
        :param incr: int - the increment value of this counter (give negative incr for counting backwards)
        :param fmt: str - an optional format parameter that follows string.format() requirements
                          Example: fmt='0x{:x}' - this will profuce strings of this look: '0x11a', '0x11b', etc.
        :param skip: int or sequence - a single int value or a sequence of int values to be skipped during counting
        """
        assert isinstance(start, int)
        assert isinstance(incr, int)
        assert fmt is None or isinstance(fmt, str)
        assert (skip is None) or isinstance(skip, int) or self._isproperskipsequence(skip), \
                    "expected int or sequence but got {}".format(type(skip).__name__)
        self._start = start
        self._incr = incr
        self._end = end
        self._fmt = fmt
        self._skip = self._arg2skipset(skip) if skip else set()
        self._current = start - incr

    def skip(self, values):
        """Adds an int value or a sequence of int values to the set of values to be skipped during counting.

        :param values: int or sequence - the value or sequence of values to be skipped
        """
        if isinstance(values, int):
            self._skip.add(values)
            return
        if self._isproperskipsequence(values):
            self._skip |= set(values)
            return
        raise TypeError("Expected int or sequence but got {}".format(type(values).__name__))

    def value(self):
        """Returns the current count value without changing the state. The value
        is formatted as ``fmt`` init argument specifies, if provided at creation."""
        if self._fmt:
            return self._fmt.format(self._current)
        return self._current

    def next(self):
        """Returns the next count value. The value is formatted as ``fmt`` init
        argument specifies, if provided at creation."""
        self._current += self._incr
        if self._end is not None and self._current == self._end:
            raise StopIteration
        while self._current in self._skip:
            self._current += self._incr
        return self.value()

    def __iter__(self):
        return self

    __next__ = next
