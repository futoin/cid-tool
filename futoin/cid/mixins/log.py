
from __future__ import print_function

from ..coloring import Coloring


class LogMixIn(object):
    __slots__ = ()

    def _info(self, msg, label=None):
        if label:  # for backward compatibility
            self._infoLabel(label, msg)
            return

        line = Coloring.info('INFO: ' + msg)
        print(line, file=self._sys.stderr)

    def _infoLabel(self, label, msg):
        line = Coloring.infoLabel(label) + Coloring.info(msg)
        print(line, file=self._sys.stderr)

    def _warn(self, msg):
        print(Coloring.warn('WARNING: ' + msg), file=self._sys.stderr)

    def _errorExit(self, msg):
        raise RuntimeError(msg)
