"""
TODO: docstring

"""
import re
from configparser import ParsingError

# regex = re.compile(r'^(tcp|udp):(all|\d{1,5}\-\d{1,5}|\d{1,5})(:\d+[a-z]{3,4})?(:\d{1,3}%)?$')
regex = re.compile(r'^(tcp|udp)(:sport|:dport)?:(all|\d{1,5}\-\d{1,5}|\d{1,5})(:\d+[a-z]{3,4})?(:\d{1,3}%)?$')


def parse_branch(branch_str):
    branch = dict()
    match = regex.match(branch_str)
    if not match:
        raise ParsingError('One or more upload/download arguments are invalid.')  # FIXME: show the offending token
    if not match.group(2) and match.group(3) != 'all':
        raise ParsingError('Value sport/dport may be omitted only if range is all.') # FIXME: show the offending token
    if not (match.group(4) or match.group(5)):
        raise ParsingError('Either rate, loss, or both must be provided.')  # FIXME: show the offending token

    branch['protocol'] = match.group(1)
    branch['porttype'] = match.group(2).lstrip(':') if match.group(2) else match.group(2)
    branch['range'] = match.group(3)
    branch['rate'] = match.group(4).lstrip(':') if match.group(4) else match.group(4)
    branch['loss'] = match.group(5).lstrip(':') if match.group(5) else match.group(5)

    return branch
