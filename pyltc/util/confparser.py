"""
PyLTC profile configuration parser module.

The PyLTC profile configuration files look like ini files at a first glance,
they are NOT standard .ini files, however.

Note that we may have repeating keys (like dclass in the second section below)
and this is not supported by the standard .ini format. The other difference is
that we have no delimiter between the option key and the value. Thus our config
section looks like a command line using full option names with double dashes
removed (and that's what it is, actually).

A sample configuration file::

 ----cut here-----------------
  [4g-sym]
  clear
  iface eth0
  dclass tcp:6000-6999:512kbit

  [3g-sym]
  clear
  iface eth0
  dclass tcp:8000-8080:96kbit
  dclass udp:5000-5080:96kbit:3%
  sclass tcp:10000-29999:256kbit:1%
  ----cut here-----------------

"""


class IllegalState(Exception):
    """Rased when a call to a method is done but the object is not
       in the proper state for that call to be allowed."""

# class MisconfigurationError(Exception):
#     """Rased when a call to a method is done but the object is not
#        in the proper state for that call to be allowed."""


class ConfigParser(object):

    def __init__(self, input=None):
        self._sections = None
        self._filename = None
        self._stream = None
        if input is None:
            return
        if isinstance(input, str):
            self._filename = input
        elif hasattr(input, 'write'):
            self._stream = input
        else:
            raise TypeError("Expecting filename (str) or file object, got %s", type(input))

    def _ensure_stream_open(self):
        if self._filename:
            return open(self._filename)
        if self._stream:
            return self._stream
        raise IllegalState("Povide filename or stream")

    def parse(self):
        with self._ensure_stream_open() as fhl:
            content = fhl.read()
        content = "\n" + content
        raw_sections = [section for section in content.split("\n[") if section]
        raw_sections = [elm.replace("\n", " --") for elm in raw_sections]
        sections = dict()
        for section in raw_sections:
            rec = [elm for elm in section.split() if elm != '--']
            sections[rec[0].rstrip("]")] = rec[1:]
        self._sections = sections
        return self

    def section(self, name):
        if not self._sections:
            raise IllegalState("Call parse() first")
        return self._sections[name]
