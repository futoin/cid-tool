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


class unzipTool(RunEnvTool):
    """list, test and extract compressed files in a ZIP archive.
"""
    __slots__ = ()

    def _installTool(self, env):
        self._install.debrpm(['unzip'])
        self._install.emerge(['app-arch/unzip'])
        self._install.pacman(['unzip'])
        self._install.apk(['unzip'])

    def initEnv(self, env, bin_name=None):
        # Busybox's version is not enough for SDKMan
        if self._detect.isAlpineLinux() and self._ospath.islink('/usr/bin/unzip'):
            return

        super(unzipTool, self).initEnv(env, bin_name)
