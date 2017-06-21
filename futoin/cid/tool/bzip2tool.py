
import os

from ..runenvtool import RunEnvTool


class bzip2Tool(RunEnvTool):
    """Freely available, patent free (see below), high-quality data compressor.

Home: http://www.bzip.org/
"""

    def _installTool(self, env):
        self._requirePackages(['bzip2'])
        self._requireEmerge(['app-arch/bzip2'])
        self._requirePacman(['bzip2'])
        self._requireApk(['bzip2'])

    def initEnv(self, env, bin_name=None):
        # Busybox's version is not enough for SDKMan
        if self._isAlpineLinux() and os.path.islink('/usr/bin/bzip2'):
            return

        super(bzip2Tool, self).initEnv(env, bin_name)
