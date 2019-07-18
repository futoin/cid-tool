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


class futoinTool(RunEnvTool):
    """futoin.json updater as defined in FTN16.

Home: https://github.com/futoin/specs/blob/master/draft/ftn16_cid_tool.md

futoin.json is the only file read by FutoIn CID itself.
"""
    __slots__ = ()
    _FUTOIN_JSON = 'futoin.json'

    def autoDetectFiles(self):
        return self._FUTOIN_JSON

    def initEnv(self, env):
        self._have_tool = True

    def updateProjectConfig(self, config, updates):
        def updater(json):
            for f in ('name', 'version'):
                if f in updates:
                    json[f] = updates[f]

        return self._pathutil.updateJSONConfig(self._FUTOIN_JSON, updater)
