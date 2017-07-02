
from ..runenvtool import RunEnvTool


class unzipTool(RunEnvTool):
    """list, test and extract compressed files in a ZIP archive.
"""
    __slots__ = ()

    def _installTool(self, env):
        self._install.debrpm(['unzip'])
        self._install.emerge(['app-arch/unzip'])
        self._install.pacman(['unzip'])
        self._install.apk(['unzip'])

    def initEnv(self, env, bin_name=None):
        # Busybox's version is not enough for SDKMan
        if self._detect.isAlpineLinux() and self._ospath.islink('/usr/bin/unzip'):
            return

        super(unzipTool, self).initEnv(env, bin_name)
