"""
Chad Phillips' (thehunmonkgroup) network simulation plugin.

Note that this NOT yet converted to an actual plugin but rather imported
as a Python module currently.

TODO: introduce plugin functionality and convert this to the first plugin ;)

"""

from pyltc.parseargs import IllegalArguments
from pyltc.target import ITarget
from pyltc.plugins.util import parse_branch
from parser import ParserError


#: netem (the qdisc that simulates special network conditions) works for a
# default of 1000 packets. This was a source of problems and the workaround
# that I came up with currently is to set it to a very large  number.
#: Chad: Beware that if you keep that filter on for too long, this limit may
# be reached.
NETEM_LIMIT = 1000000000


def shape_ports(target, direction, range, rate, loss=None):
    """
    The only recipe that we support currently. Creates a LTC (egress) chain
    that shapes the traffic for a range of tcp ports into a given rate using
    htb. If loss is provided, adds simulated jitter using netem.
    """
    rootqd = target.set_root_qdisc('htb')
    htbclass = target.add_class('htb', parent=rootqd, rate=rate)
    if loss:
        target.add_qdisc('netem', parent=htbclass, loss=loss, limit=NETEM_LIMIT) # e.g. 'loss random 7%'
    assert range.count("-") == 1, "illegal range: {!r}".format(range)   # we do not yet support complex ranges
    start, end = (int(elm) for elm in range.split("-"))
    accepted_values = ('dport', 'sport')
    assert direction in accepted_values, \
            "direction ({!r}) must be one of {!r}".format(direction, accepted_values)
    offset = 0 if direction == 'sport' else 2
    cond = '"cmp(u16 at {} layer transport gt {}) and cmp(u16 at {} layer transport lt {})"' \
            .format(offset, start - 1, offset, end + 1)
    target.add_filter('basic', rootqd, cond=cond, flownode=htbclass)


def threefold(target, range, rate, loss=None):  # TODO: Unused?
    """HTB-based hirarchical system."""
    rootqd = target.set_root_qdisc('htb', default=1)
    default_class = target.add_class('htb', parent=rootqd)
    default_qdisc = target.add_qdisc('pfifo', parent=default_class, limit=4096)
    shaped_class = target.add_class('htb', parent=rootqd, rate=rate)
    assert range.count("-") == 1, "illegal range: {!r}".format(range)   # we do not yet support complex ranges
    start, end = (int(elm) for elm in range.split("-"))
    offset = 2 # dpoort
    cond = '"cmp(u16 at {} layer transport gt {}) and cmp(u16 at {} layer transport lt {})"' \
            .format(offset, start - 1, offset, end + 1)
    target.add_filter('basic', rootqd, cond=cond, flownode=shaped_class)


def shape_dports(chain, range, rate, loss=None):  # TODO: Unused?
    return chain.shape_ports('dport', range, rate, loss)


def shape_sports(chain, range, rate, loss=None):  # TODO: Unused?
    return chain.shape_ports('sport', range, rate, loss)


def build_basics(target, tcp_all_rate, udp_all_rate):
    root_qdisc = target.set_root_qdisc('htb')

    tcp_rate = tcp_all_rate if tcp_all_rate else '15gbit'
    udp_rate = udp_all_rate if udp_all_rate else '15gbit'
    tcp_class = target.add_class('htb', root_qdisc, rate=tcp_rate)
    udp_class = target.add_class('htb', root_qdisc, rate=udp_rate)

    tcp_filter = target.add_filter('u32', root_qdisc, cond="ip protocol 6 0xff", flownode=tcp_class)
    udp_filter = target.add_filter('u32', root_qdisc, cond="ip protocol 17 0xff", flownode=udp_class)

    tcp_qdisc = target.add_qdisc('htb', tcp_class)
    udp_qdisc = target.add_qdisc('htb', udp_class)

    return tcp_qdisc, udp_qdisc


def build_range_filters(target, parent, flownode, port_range, offset):
    # tc filter add dev ifb0 protocol ip parent 2:0 prio 1 u32 match ip dport 5001 0xffff flowid 2:1
    port_dir = 'dport' if offset == 2 else 'sport'
    if '-' in port_range:
        start, end = map(int, port_range.split('-'))
        for port in range(start, end + 1):
            target.add_filter('u32', parent, 'ip {} {} 0xffff'.format(port_dir, port), flownode)
    else:
        target.add_filter('u32', parent, 'ip {} {} 0xffff'.format(port_dir, port_range), flownode)


# def parse_branch_list(args_list):
#     branches = list()
#     for args_str in args_list:
#         current = {'protocol': None, 'range': None, 'rate': None, 'loss': None}
#         for token in args_str.split(':'):
#             if '-' in token or token.isdigit():
#                 current['range'] = token
#             elif token.endswith('bit') or token.endswith('bps'):
#                 current['rate'] = token
#             elif token.endswith('%'):
#                 current['loss'] = token
#             elif token in ('tcp', 'udp'):
#                 current['protocol'] = token
#             else: # unrecognizable protocol or nothing will be treated as tcp #FIXME: Is this alright?
#                 current['protocol'] = 'tcp'
#         branches.append(current)
#     return branches


def parse_branch_list(args_list):
    branches = list()
    for args_str in args_list:
        current = parse_branch(args_str)
        branches.append(current)
    return branches


def build_tree(target, tcphook, udphook, args_list, offset, is_ingress=False):
    branches = parse_branch_list(args_list)
    for branch in branches:
        if branch['range'] == 'all':
            continue

        if branch['protocol'] == 'tcp':
            hook = tcphook
        elif branch['protocol'] == 'udp':
            hook = udphook
        else:
            raise IllegalArguments("protocol not specified (tcp or udp?)")  # FIXME: revisit this
            #raise RuntimeError('UNREACHABLE')

        # class(htb) - shaping
        rate = branch['rate'] if branch['rate'] else '15gbit'  # TODO: move this to a constant
        htb_class = target.add_class('htb', hook, rate=rate)
        # filter(basic) - port
        if is_ingress or '-' not in branch['range']:
            build_range_filters(target, hook, htb_class, branch['range'], offset)  # FIXME: use better means to communicate dport/sport case
        else:
            start, end = (int(elm) for elm in branch['range'].split("-"))
            cond_port_range = '"cmp(u16 at {} layer transport gt {}) and cmp(u16 at {} layer transport lt {})"' \
                         .format(offset, start - 1, offset, end + 1)
            basic_filter = target.add_filter('basic', hook, cond=cond_port_range, flownode=htb_class)
        # qdisc(netem) - loss
        if branch['loss']:
            netem_qdisc = target.add_qdisc('netem', parent=htb_class, loss=branch['loss'], limit=NETEM_LIMIT)


def determine_all_rates(dclasses, sclasses):
    tcp_all_rate = False # serves as flag too
    udp_all_rate = False # serves as flag too
    for classes in (dclasses, sclasses):
        if not classes:
            continue
        for some_class in classes:
            parsed = parse_branch(some_class)
            if parsed['range'] == 'all' and parsed['protocol'] == 'tcp':
                if tcp_all_rate:
                    raise ParserError("More than one 'all' range detected for the same protocol(tcp).")
                tcp_all_rate = parsed['rate']
            elif parsed['range'] == 'all' and parsed['protocol'] == 'udp':
                if udp_all_rate:
                    raise ParserError("More than one 'all' range detected for the same protocol(udp).")
                udp_all_rate = parsed['rate']
    return tcp_all_rate, udp_all_rate

ITarget.shape_ports = shape_ports
ITarget.shape_dports = shape_dports
ITarget.shape_sports = shape_sports


def plugin_main(args, iface, ifbdev):
    chain = ifbdev.egress if args.ingress else iface.egress
    if args.clear:
        if args.ingress:
            iface.ingress.clear(is_ingress=True)
        chain.clear()
    if args.dclass or args.sclass:
        if args.ingress:
            cmd = 'tc qdisc add dev {} handle ffff: ingress'.format(iface.name)
            chain._commands.append(cmd)
            cmd = ("tc filter add dev {} parent ffff: protocol ip"
                   + " u32 match u32 0 0 action mirred egress redirect dev {}").format(iface.name, ifbdev.name)
            chain._commands.append(cmd)
        tcp_all_rate, udp_all_rate = determine_all_rates(args.dclass, args.sclass)
        tcp_hook, udp_hook = build_basics(chain, tcp_all_rate, udp_all_rate)
    if args.dclass:
        build_tree(chain, tcp_hook, udp_hook, args.dclass, offset=2, is_ingress=bool(args.ingress))
    if args.sclass:
        build_tree(chain, tcp_hook, udp_hook, args.sclass, offset=0, is_ingress=bool(args.ingress))
    iface.ingress.install(verbose=args.verbose)
    chain.install(verbose=args.verbose)
