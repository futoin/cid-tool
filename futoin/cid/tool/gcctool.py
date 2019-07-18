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


class gccTool(RunEnvTool):
    """GNU Compiler Collection.

Home: https://gcc.gnu.org/

If gccBin is set it must point to bin folder.
"""
    __slots__ = ()

    def envNames(self):
        return ['gccBin', 'gccPrefix', 'gccPostfix']

    def _installTool(self, env):
        self._install.deb(['gcc'])
        self._install.rpm(['gcc'])
        self._install.emerge(['sys-devel/gcc'])
        self._install.pacman(['gcc'])
        self._install.apk(['gcc'])

    def initEnv(self, env):
        gcc_bin = env.get('gccBin', None)

        pref = env.setdefault('gccPrefix', '')
        postf = env.setdefault('gccPostfix', '')

        if gcc_bin:
            if self._ospath.exists(gcc_bin):
                self._have_tool = True
        else:
            gcc = pref + 'gcc' + postf
            gcc = self._pathutil.which(gcc)

            if gcc:
                env['gccBin'] = gcc
                self._have_tool = True
