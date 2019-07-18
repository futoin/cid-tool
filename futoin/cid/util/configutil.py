#
# Copyright 2015-2019 Andrey Galkin <andrey@futoin.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from collections import OrderedDict
from ..mixins.ondemand import ext as _ext

# ==================


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


def requestsOptions(env, kwargs):
    kwargs['timeout'] = timeouts(env, 'requests')
    headers = kwargs.setdefault('headers', {})
    headers['User-Agent'] = 'FutoIn CID'


# ==================
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
# ==================


def listify(val):
    if isinstance(val, list):
        return val

    return [val]


# ==================


def parseJSON(val):
    return _ext.json.loads(val, object_pairs_hook=lambda pairs: OrderedDict(pairs))

# ==================


def deepMerge(target, source):
    for k, v in source.items():
        if isinstance(v, dict):
            # get node or create one
            t = target.setdefault(k, OrderedDict())
            deepMerge(t, v)
        elif isinstance(v, list):
            t = target.setdefault(k, [])
            t.extend(v)
        else:
            target[k] = v

    return target

# ==================


def syslogTag(env, name):
    tag = env.get('syslogTag', None)

    if tag:
        return '{0}-{1}'.format(tag, name)

    return name
