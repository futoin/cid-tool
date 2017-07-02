
from ..runenvtool import RunEnvTool


class bzip2Tool(RunEnvTool):
    """Freely available, patent free (see below), high-quality data compressor.

Home: http://www.bzip.org/
"""
    __slots__ = ()

    def _installTool(self, env):
        self._install.debrpm(['bzip2'])
        self._install.emerge(['app-arch/bzip2'])
        self._install.pacman(['bzip2'])
        self._install.apk(['bzip2'])
        self._install.brew('bzip2')

    def initEnv(self, env, bin_name=None):
        # Busybox's version is not enough for SDKMan
        if self._detect.isAlpineLinux() and self._ospath.islink('/usr/bin/bzip2'):
            return

        super(bzip2Tool, self).initEnv(env, bin_name)
