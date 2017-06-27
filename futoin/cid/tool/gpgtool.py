
from ..runenvtool import RunEnvTool


class gpgTool(RunEnvTool):
    """The GNU Privacy Guard.

Home: https://www.gnupg.org/

gpgKeyServer is hkp://keyserver.ubuntu.com:80 by default
"""

    def envNames(self):
        return ['gpgBin', 'gpgKeyServer']

    def _installTool(self, env):
        self._requirePackages(['gnupg', 'gnupg2'])
        self._requireEmerge(['app-crypt/gnupg'])
        self._requirePacman(['gnupg'])
        self._requireApk(['gnupg'])
        self._requireBrew('gnupg')

    def initEnv(self, env):
        super(gpgTool, self).initEnv(env)
        env.setdefault('gpgKeyServer', 'hkp://keyserver.ubuntu.com:80')
