#
# Copyright 2015-2019 Andrey Galkin <andrey@futoin.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

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
