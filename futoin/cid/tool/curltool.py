
from ..runenvtool import RunEnvTool


class curlTool(RunEnvTool):
    """Command line tool and library for transferring data with URLs.

Home: https://curl.haxx.se/
"""

    def _installTool(self, env):
        self._requirePackages(['curl'])
        self._requireEmerge(['net-misc/curl'])
        self._requirePacman(['curl'])
        self._requireApk(['curl'])
        self._requireBrew('curl')
