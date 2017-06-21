
import os

from ..runenvtool import RunEnvTool


class tarTool(RunEnvTool):
    """The GNU version of the tar archiving utility.
"""

    def _installTool(self, env):
        self._requirePackages(['tar'])
        self._requireEmerge(['app-arch/tar'])
        self._requirePacman(['tar'])
        self._requireApk(['tar'])

    def initEnv(self, env, bin_name=None):
        # Busybox's version is not enough for SDKMan
        if self._isAlpineLinux() and os.path.islink('/bin/tar'):
            return

        super(tarTool, self).initEnv(env, bin_name)
