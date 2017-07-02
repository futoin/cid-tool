
from ..runenvtool import RunEnvTool


class xzTool(RunEnvTool):
    """Free general-purpose data compression software with a high compression ratio.

Home: https://tukaani.org/xz/
"""
    __slots__ = ()

    def _installTool(self, env):
        self._install.debrpm(['xz-utils'])
        self._install.emerge(['app-arch/xz-utils'])
        self._install.pacman(['xz-utils'])
        self._install.apk(['xz'])
        self._install.brew('xz')
