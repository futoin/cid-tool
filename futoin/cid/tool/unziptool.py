
import os

from ..runenvtool import RunEnvTool


class unzipTool(RunEnvTool):
    """list, test and extract compressed files in a ZIP archive.
"""

    def _installTool(self, env):
        self._requirePackages(['unzip'])
        self._requireEmerge(['app-arch/unzip'])
        self._requirePacman(['unzip'])
        self._requireApk(['unzip'])

    def initEnv(self, env, bin_name=None):
        # Busybox's version is not enough for SDKMan
        if self._isAlpineLinux() and os.path.islink('/usr/bin/unzip'):
            return

        super(unzipTool, self).initEnv(env, bin_name)
