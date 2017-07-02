
from ..runenvtool import RunEnvTool


class gzipTool(RunEnvTool):
    """Compression utility designed to be a replacement for compress.

Home: http://www.gzip.org/
"""
    __slots__ = ()

    def _installTool(self, env):
        self._install.debrpm(['gzip'])
        self._install.emerge(['app-arch/gzip'])
        self._install.pacman(['gzip'])
        self._install.apk(['gzip'])
        self._install.brew('gzip')

    def initEnv(self, env, bin_name=None):
        # Busybox's version is not enough for SDKMan
        if self._detect.isAlpineLinux() and self._ospath.islink('/bin/gzip'):
            return

        super(gzipTool, self).initEnv(env, bin_name)
