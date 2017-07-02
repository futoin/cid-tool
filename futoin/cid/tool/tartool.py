
from ..runenvtool import RunEnvTool


class tarTool(RunEnvTool):
    """The GNU version of the tar archiving utility.
"""
    __slots__ = ()

    def _installTool(self, env):
        self._install.debrpm(['tar'])
        self._install.emerge(['app-arch/tar'])
        self._install.pacman(['tar'])
        self._install.apk(['tar'])
        self._install.brew('gnu-tar')

    def initEnv(self, env, bin_name=None):
        # Busybox's version is not enough for SDKMan
        if self._detect.isAlpineLinux() and self._ospath.islink('/bin/tar'):
            return

        super(tarTool, self).initEnv(env, bin_name)
