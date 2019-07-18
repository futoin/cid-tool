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

from ..buildtool import BuildTool


class makeTool(BuildTool):
    """GNU Make.

Home: https://www.gnu.org/software/make/

Expects presence of "clean" target.
Build uses the default target.
"""
    __slots__ = ()

    def autoDetectFiles(self):
        return [
            'GNUmakefile',
            'makefile',
            'Makefile',
        ]

    def _installTool(self, env):
        self._install.debrpm(['make'])
        self._install.emerge(['sys-devel/make'])
        self._install.pacman(['make'])
        self._install.apk(['make'])

    def onPrepare(self, config):
        cmd = [config['env']['makeBin'], 'clean']
        self._executil.callMeaningful(cmd)

    def onBuild(self, config):
        target = self._getTune(config, 'build')

        if target:
            args = [target]
        else:
            args = []

        cmd = [config['env']['makeBin']] + args
        self._executil.callMeaningful(cmd)
