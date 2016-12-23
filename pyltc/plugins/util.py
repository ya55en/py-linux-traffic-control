def parse_branch(branch_str):
    branch = {'protocol': None, 'range': None, 'rate': None, 'loss': None}
    for token in branch_str.split(':'):
        if '-' in token or token.isdigit() or token=='all':
            branch['range'] = token
        elif token.endswith('bit') or token.endswith('bps'):
            branch['rate'] = token
        elif token.endswith('%'):
            branch['loss'] = token
        elif token in ('tcp', 'udp'):
            branch['protocol'] = token
        else:
            raise ValueError('Unknown protocol {!r}'.format(token))
    return branch