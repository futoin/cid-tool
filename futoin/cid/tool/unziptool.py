
from ..runenvtool import RunEnvTool


class unzipTool(RunEnvTool):
    """list, test and extract compressed files in a ZIP archive.
"""
    __slots__ = ()

    def _installTool(self, env):
        self._requirePackages(['unzip'])
        self._requireEmerge(['app-arch/unzip'])
        self._requirePacman(['unzip'])
        self._requireApk(['unzip'])

    def initEnv(self, env, bin_name=None):
        # Busybox's version is not enough for SDKMan
        if self._isAlpineLinux() and self._ospath.islink('/usr/bin/unzip'):
            return

        super(unzipTool, self).initEnv(env, bin_name)
