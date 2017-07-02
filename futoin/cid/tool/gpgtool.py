
from ..runenvtool import RunEnvTool


class gpgTool(RunEnvTool):
    """The GNU Privacy Guard.

Home: https://www.gnupg.org/

gpgKeyServer is hkp://keyserver.ubuntu.com:80 by default
"""
    __slots__ = ()

    def envNames(self):
        return ['gpgBin', 'gpgKeyServer']

    def _installTool(self, env):
        self._install.debrpm(['gnupg', 'gnupg2'])
        self._install.emerge(['app-crypt/gnupg'])
        self._install.pacman(['gnupg'])
        self._install.apk(['gnupg'])
        self._install.brew('gnupg')

    def initEnv(self, env):
        super(gpgTool, self).initEnv(env)
        env.setdefault('gpgKeyServer', 'hkp://keyserver.ubuntu.com:80')
