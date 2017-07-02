
from ..util.log import *

__all__ = ('LogMixIn')


class LogMixIn(object):
    __slots__ = ()

    def _info(self, msg, label=None):
        if label:  # for backward compatibility
            infoLabel(label, msg)
        else:
            info(msg)

    def _infoLabel(self, label, msg):
        infoLabel(label, msg)

    def _warn(self, msg):
        warn(msg)

    def _errorExit(self, msg):
        errorExit(msg)
