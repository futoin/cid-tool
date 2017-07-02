
from ..runenvtool import RunEnvTool


class curlTool(RunEnvTool):
    """Command line tool and library for transferring data with URLs.

Home: https://curl.haxx.se/
"""
    __slots__ = ()

    def _installTool(self, env):
        self._install.debrpm(['curl'])
        self._install.emerge(['net-misc/curl'])
        self._install.pacman(['curl'])
        self._install.apk(['curl'])
        self._install.brew('curl')
