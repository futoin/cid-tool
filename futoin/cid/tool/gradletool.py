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
from .sdkmantoolmixin import SdkmanToolMixIn


class gradleTool(SdkmanToolMixIn, BuildTool):
    """Gradle Build Tool.

Home: https://gradle.org/

Build targets:
    prepare -> clean
    build -> <default> without explicit target
    package -> dists
    packageGlob -> '*.jar'
Override targets with .config.toolTune.

Requires Java >= 7.
"""
    __slots__ = ()

    def _minJava(self):
        return '7'

    def autoDetectFiles(self):
        return 'build.gradle'

    def envDeps(self, env):
        super(gradleTool, self).envDeps(env)

        gradlew_prop = 'gradle/wrapper/gradle-wrapper.properties'

        if self._ospath.exists(gradlew_prop):
            with open(gradlew_prop, 'r') as f:
                props = f.read()
                gradleVer = self._ext.re.search(
                    'gradle-([0-9.]+)-(all|bin).zip', props)

                if gradleVer is None:
                    self._errorExit(
                        'Unable to find gradle version in {0}'.format(gradlew_prop))

                env['gradleVer'] = gradleVer.group(1)

    def onPrepare(self, config):
        target = self._getTune(config, 'prepare', 'clean')
        cmd = [config['env']['gradleBin'],
               '-q', '--no-daemon', target]
        self._executil.callMeaningful(cmd)

    def onBuild(self, config):
        target = self._getTune(config, 'build')

        if target:
            args = [target]
        else:
            args = []

        cmd = [config['env']['gradleBin'],
               '-q', '--no-daemon'] + args
        self._executil.callMeaningful(cmd)

    def onPackage(self, config):
        target = self._getTune(config, 'package', 'dists')
        cmd = [config['env']['gradleBin'],
               '-q', '--no-daemon', target]
        self._executil.callMeaningful(cmd)

        packageGlob = self._getTune(config, 'packageGlob', 'build/libs/*.jar')
        self._pathutil.addPackageFiles(config, packageGlob)
