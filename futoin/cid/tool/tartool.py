
from ..runenvtool import RunEnvTool


class tarTool(RunEnvTool):
    """The GNU version of the tar archiving utility.
"""
    __slots__ = ()

    def _installTool(self, env):
        self._requirePackages(['tar'])
        self._requireEmerge(['app-arch/tar'])
        self._requirePacman(['tar'])
        self._requireApk(['tar'])
        self._requireBrew('gnu-tar')

    def initEnv(self, env, bin_name=None):
        # Busybox's version is not enough for SDKMan
        if self._isAlpineLinux() and self._ospath.islink('/bin/tar'):
            return

        super(tarTool, self).initEnv(env, bin_name)
