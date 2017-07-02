
from ..runenvtool import RunEnvTool


class sshTool(RunEnvTool):
    """Secure Shell client.

Home: https://www.openssh.com/

Note:
    * sshStrictHostKeyChecking is set to "yes" by default.
      It is used by tools depending on ssh.
"""
    __slots__ = ()

    def envNames(self):
        return ['sshBin', 'sshStrictHostKeyChecking']

    def _installTool(self, env):
        self._install.deb(['openssh-client'])
        self._install.rpm(['openssh'])
        self._install.emerge(['virtual/ssh'])
        self._install.pacman(['openssh'])
        self._install.apk('openssh-client')

    def initEnv(self, env):
        env.setdefault('sshStrictHostKeyChecking', 'yes')
        super(sshTool, self).initEnv(env)
