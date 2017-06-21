
import os

from ..runenvtool import RunEnvTool


class sshTool(RunEnvTool):
    """Secure Shell client.

Home: https://www.openssh.com/

Note:
    * sshStrictHostKeyChecking is set to "yes" by default.
      It is used by tools depending on ssh.
"""

    def envNames(self):
        return ['sshBin', 'sshStrictHostKeyChecking']

    def _installTool(self, env):
        self._requireDeb(['openssh-client'])
        self._requireRpm(['openssh'])
        self._requireEmerge(['virtual/ssh'])
        self._requirePacman(['openssh'])
        self._requireApk('openssh-client')

    def initEnv(self, env):
        env.setdefault('sshStrictHostKeyChecking', 'yes')
        super(sshTool, self).initEnv(env)
