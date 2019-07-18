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
from .npmtoolmixin import NpmToolMixIn


class webpackTool(NpmToolMixIn, BuildTool):
    """webpack is a module bundler (JS world)

Home: https://webpack.js.org
"""
    __slots__ = ()

    def autoDetectFiles(self):
        return 'webpack.config.js'

    def onBuild(self, config):
        webpackBin = config['env']['webpackBin']
        cmd = [webpackBin, '-p', '--profile', '--display', '--verbose']
        self._executil.callMeaningful(cmd)
