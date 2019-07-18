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


class curlTool(RunEnvTool):
    """Command line tool and library for transferring data with URLs.

Home: https://curl.haxx.se/
"""
    __slots__ = ()

    def _installTool(self, env):
        self._install.debrpm(['curl'])
        self._install.emerge(['net-misc/curl'])
        self._install.pacman(['curl'])
        self._install.apk(['curl'])
        self._install.brew('curl')
