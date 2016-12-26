"""
tc rate string splitter / validator.
See http://man7.org/linux/man-pages/man8/tc.8.html#PARAMETERS
"""
import re

_MAN_PAGE_DUMP = """
    bit or a bare number
           Bits per second

    kbit   Kilobits per second

    mbit   Megabits per second

    gbit   Gigabits per second

    tbit   Terabits per second

    bps    Bytes per second

    kbps   Kilobytes per second

    mbps   Megabytes per second

    gbps   Gigabytes per second

    tbps   Terabytes per second
"""

# YD: Kept for reference; do not remove for now
# _SI_UNITS = set([token for token in _MAN_PAGE_DUMP.split() if token.endswith('bit') or token.endswith('bps')])
# _IEC_UNITS = set()
# for units in _SI_UNITS:
#     if len(units) == 4:
#         _IEC_UNITS.add(units[0] + "i" + units[1:])

#: _UNITS == {'kibit', 'kbit', 'mibit', 'gibit', 'bps', 'mbps', 'tbps', 'gibps', 'kbps', 'gbps', 'gbit',
#:            'kibps', 'tibps', 'mibps', 'mbit', 'bit', 'tbit', 'tibit'}
#_UNITS = _SI_UNITS | _IEC_UNITS


#: Rate units table. Used this to verify: http://www.matisse.net/bitcalc/
_UNITS = _RATE_KOEFF = {
    'bit': 1,
    'bps': 8,
    'kbit': 1000,
    'kibit': 1024,
    'kbps': 8 * 1000,
    'kibps': 8 * 1024,
    'mbit': 1000 * 1000,
    'mibit': 1024 * 1024,
    'mbps': 8 * 1000 * 1000,
    'mibps': 8 * 1024 * 1024,
    'gbit': 1000 * 1000 * 1000,
    'gibit': 1024 * 1024 * 1024,
    'gbps': 8 * 1000 * 1000 * 1000,
    'gibps': 8 * 1024 * 1024 * 1024,
    'tbit': 1000 * 1000 * 1000 * 1000,
    'tibit': 1024 * 1024 * 1024 * 1024,
    'tbps': 8 * 1000 * 1000 * 1000 * 1000,
    'tibps': 8 * 1024 * 1024 * 1024 * 1024,
}


def split_rate(ratestr, validate=False):
    """Splits given rate string and returns a two-element tuple (rate:int, units:str).
       Will optionally validate the rate string given if validate is True."""

    regex = re.compile("^(\d+)([a-z]+)$")
    match = regex.match(ratestr)
    if not match:
        raise ValueError("Illegal rate string: {!r}".format(ratestr))
    rate = match.group(1)
    units = match.group(2)
    if validate and units not in _UNITS.keys():
        raise ValueError("Illegal rate string: {!r}".format(ratestr))
    return int(rate), units


def convert2bps(ratestr, valildate=True):
    """Returns an integer equal to bits per second equivalent to the given rate
       in SI or IEC units as understood by tc."""
    rate, units = split_rate(ratestr, valildate)
    return rate * _RATE_KOEFF[units]
