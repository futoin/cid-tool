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

from ..runtimetool import RuntimeTool
from .sdkmantoolmixin import SdkmanToolMixIn


class scalaTool(SdkmanToolMixIn, RuntimeTool):
    """The Scala Programming Language.

Home: https://www.scala-lang.org/

Installed via SDKMan!

Requires Java >= 8.
"""
    __slots__ = ()

    def _minJava(self):
        return '8'

    def tuneDefaults(self, env):
        return {
            'minMemory': '256M',
            'debugOverhead': '128M',
            'connMemory': '100K',
            'debugConnOverhead': '1M',
            'socketType': 'tcp',
            'scalable': False,
            'reloadable': False,
            'multiCore': True,
        }
