"""
Pyltc pluguins' common helpers.

(Currently serves the one and only ``simnet`` plugin.)

"""
import re
from functools import lru_cache
from configparser import ParsingError

regex = re.compile(r'^(tcp|udp)(:sport|:dport|:lport|:rport)?:(all|\d{1,5}\-\d{1,5}|\d{1,5})(:\d+[a-z]{3,4})?(:\d{1,3}%)?$')


class BranchParser(object):

    def __init__(self, branch_str, download=None, upload=None, dontcare=False):
        if not dontcare and ((download is True) == (upload is True)):
            message = "Exactly one of download={!r}, upload={!r} must be set to True".format(download, upload)
            raise TypeError(message)
        self._branch = None
        self._upload = bool(upload)
        self._dontcare = dontcare
        self._do_parse(branch_str)

    def _do_parse(self, branch_str):
        match = regex.match(branch_str)
        if not match:
            raise ParsingError("Invalid upload/download argument: {!r}".format(branch_str))
        if not match.group(2) and match.group(3) != 'all':
            raise ParsingError("Port type not found in {!r} (may be omitted only if range is 'all')".format(branch_str))
        if not (match.group(4) or match.group(5)):
            raise ParsingError('Either RATE, JITTER or both must be present in {!r}'.format(branch_str))
        self._branch = dict()
        self._branch['protocol'] = match.group(1)
        orig_porttype = match.group(2).lstrip(':') if match.group(2) else match.group(2)
        self._branch['porttype'] = self._deduce_port_type(orig_porttype)
        self._branch['range'] = match.group(3)
        self._branch['rate'] = match.group(4).lstrip(':') if match.group(4) else match.group(4)
        self._branch['loss'] = match.group(5).lstrip(':') if match.group(5) else match.group(5)

    def _deduce_port_type(self, porttype):
        """'lport' will be resolved to 'sport' in case of egress case (upload) and 'dport' for ingress (download).
        'rport' is the reverse -- resolves to 'dport' in case of egress case (upload) and 'sport' for ingress (download).
        :param porttype: string - the parsed port type, one of 'sport', 'dport', 'lport', 'rport'
        :return: string - deduced actual port type, one of 'sport', 'dport'
        """
        if porttype is None:  # for the 'all' port range case
            return None

        if porttype in ('sport', 'dport'):
            return porttype

        if porttype in ('lport', 'rport'):
            if porttype == 'lport':
                return 'sport' if self._upload else 'dport'
            if porttype == 'rport':
                return 'dport' if self._upload else 'sport'
            raise RuntimeError("UNREACHABLE!")

        message = "porttype={!r} must be one of 'sport', 'dport', 'lport', 'rport'".format(porttype)
        raise AssertionError(message)

    @lru_cache(maxsize=1)
    def as_dict(self):
        # We return a copy which is lru-cached as well. If someone messes up with the copy,
        # that will affect other as_dict() calls but self._branch will remain intact.
        return self._branch.copy()

    def __getattr__(self, name):
        try:
            return self._branch[name]
        except KeyError:
            raise AttributeError("{!r} object has no attribute {!r}".format(type(self).__name__, name))
