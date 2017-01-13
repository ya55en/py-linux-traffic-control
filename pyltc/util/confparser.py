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


class ConfigSyntaxError(Exception):
    pass


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
        raise IllegalState("Provide filename or stream")

    def _strip_comments(self):

        def find_comment_start(line):
            return min((line + "#").find("#"), (line + ";").find(";"))

        with self._ensure_stream_open() as fhl:
            for line in fhl:
                sig_part = line[:find_comment_start(line)]
                if not sig_part.strip():
                    yield ""
                yield sig_part

    def _preparse(self):
        current_line = 'init'
        for line in self._strip_comments():
            #print('@ "' + line + '"')
            if not line.strip():
                continue
            if line.startswith(" "):  # FIXME: support also \t
                if current_line == 'init':
                    raise RuntimeError("Invalid configuration file.")
                current_line += " " + line.strip()
                continue
            if current_line and current_line != 'init':
                yield current_line
            current_line = line.rstrip()
        yield current_line

    def parse(self):
        section = None
        sections = dict()

        def process_line(line):
            nonlocal section, sections
            if not line.strip(""):
                return
            if line.startswith("["):
                if not line.endswith("]"):
                    raise ConfigSyntaxError("malformed section header in line %r", line)
                sections[line[1:-1]] = section = list()
            elif line.find("]") != -1:
                raise ConfigSyntaxError("malformed section header in line %r", line)
            else:
                if section is None:
                    raise ConfigSyntaxError("options without section in line {!r}".format(line))
                tokens = line.split()
                tokens[0] = "--" + tokens[0]
                section.extend(tokens)

        for line in self._preparse():
            #print(line)
            process_line(line)
        self._sections = sections
        return self

    def section(self, name):
        if not self._sections:
            raise IllegalState("Call parse() first")
        return self._sections[name]

