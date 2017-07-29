"""
Miscellaneous utility stuff.

"""


class SimpleNamespace(object):
    """Simple namespace with a handy ``repr`` method."""
    def __repr__(self):
        return "<SimpleNamespace({!r}) at 0x{:016x}>".format(self.__dict__, id(self))


class UndefType(object):
    """A type for an single ``Undef`` instance."""

Undef = UndefType()
