
#==================


def timeouts(env, fmt):
    timeouts = env['timeouts']
    connect_to = int(timeouts['connect'])
    read_to = int(timeouts['read'])
    total_to = int(timeouts['total'])

    if fmt == 'requests':
        return (connect_to, read_to)
    elif fmt == 'curl':
        return [
            '--connect-timeout', '{0}'.format(int(connect_to)),
            '--max-time', '{0}'.format(int(total_to)),
        ]

    raise NotImplementedError('Unknown format: {0}'.format(fmt))


#==================
_memory_mult_table = {
    'B': 1,
    'K': (1 << 10),
    'M': (1 << 20),
    'G': (1 << 30),
}


def parseMemory(val):
    b = int(val[:-1])
    m = _memory_mult_table[val[-1]]

    if b <= 0:
        raise ValueError('Memory must be positive')

    return b * m


def toMemory(val):
    res = None
    old_v = 0

    for (k, v) in _memory_mult_table.items():
        if val % v:
            continue
        elif v > old_v:
            res = '{0}{1}'.format(int(val / v), k)
            old_v = v

    return res
#==================


def listify(val):
    if isinstance(val, list):
        return val

    return [val]
