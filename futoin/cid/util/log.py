
from __future__ import print_function

from ..coloring import Coloring
from ..mixins.ondemand import ext as _ext


def info(msg, label=None):
    if label:  # for backward compatibility
        infoLabel(label, msg)
        return

    line = Coloring.info('INFO: ' + msg)
    print(line, file=_ext.sys.stderr)


def infoLabel(label, msg):
    line = Coloring.infoLabel(label) + Coloring.info(msg)
    print(line, file=_ext.sys.stderr)


def warn(msg):
    print(Coloring.warn('WARNING: ' + msg), file=_ext.sys.stderr)


def errorExit(msg):
    raise RuntimeError(msg)
