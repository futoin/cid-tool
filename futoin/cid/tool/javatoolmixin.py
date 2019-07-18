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


class JavaToolMixIn(object):
    __slots__ = ()

    _LATEST_JAVA = '8'

    def _minJava(self):
        return False

    def envDeps(self, env):
        min_java = self._minJava()

        if not min_java:
            return

        for ek in ['javaVer', 'jdkVer']:
            if env.get(ek, None):
                if int(env[ek]) < int(min_java):
                    self._errorExit('{0} requires minimal {1}={2}'
                                    .format(self._name, ek, min_java))
            else:
                env[ek] = str(self._LATEST_JAVA)
