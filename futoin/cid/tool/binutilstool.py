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


class binutilsTool(RunEnvTool):
    """GNU Binutils.

Home: https://www.gnu.org/software/binutils/

If binutilsDir is set it must point to bin folder.
"""
    __slots__ = ()

    def envNames(self):
        return ['binutilsDir', 'binutilsPrefix', 'binutilsPostfix']

    def _installTool(self, env):
        self._install.deb(['binutils'])
        self._install.rpm(['binutils'])
        self._install.emerge(['sys-devel/binutils'])
        self._install.pacman(['binutils'])
        self._install.apk(['binutils'])

    def initEnv(self, env):
        ospath = self._ospath
        pref = env.setdefault('binutilsPrefix', '')
        postf = env.setdefault('binutilsPostfix', '')

        bu_dir = env.get('binutilsDir', None)
        ld = pref + 'ld' + postf

        if bu_dir:
            ld = ospath.join(bu_dir, ld)
            self._have_tool = ospath.exists(bu_dir)
        else:
            ld = self._pathutil.which(ld)

            if ld:
                env['binutilsDir'] = ospath.dirname(ld)
                self._have_tool = True
