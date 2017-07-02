
from ..runenvtool import RunEnvTool


class gzipTool(RunEnvTool):
    """Compression utility designed to be a replacement for compress.

Home: http://www.gzip.org/
"""
    __slots__ = ()

    def _installTool(self, env):
        self._requirePackages(['gzip'])
        self._requireEmerge(['app-arch/gzip'])
        self._requirePacman(['gzip'])
        self._requireApk(['gzip'])
        self._requireBrew('gzip')

    def initEnv(self, env, bin_name=None):
        # Busybox's version is not enough for SDKMan
        if self._isAlpineLinux() and self._ospath.islink('/bin/gzip'):
            return

        super(gzipTool, self).initEnv(env, bin_name)
