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


class gpgTool(RunEnvTool):
    """The GNU Privacy Guard.

Home: https://www.gnupg.org/

gpgKeyServer is hkp://keyserver.ubuntu.com:80 by default
"""
    __slots__ = ()

    def envNames(self):
        return ['gpgBin', 'gpgKeyServer']

    def _installTool(self, env):
        self._install.debrpm('gnupg')
        self._install.debrpm('gnupg2')
        self._install.debrpm('dirmngr')

        self._install.emerge(['app-crypt/gnupg'])
        self._install.pacman(['gnupg'])
        self._install.apk(['gnupg'])
        self._install.brew('gnupg')

    def initEnv(self, env):
        super(gpgTool, self).initEnv(env)
        env.setdefault('gpgKeyServer', 'hkp://keyserver.ubuntu.com:80')

        if self._have_tool and self._detect.isDeb():
            self._have_tool = self._pathutil.which('dirmngr')
