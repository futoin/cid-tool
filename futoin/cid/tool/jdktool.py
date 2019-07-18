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
from .javatoolmixin import JavaToolMixIn


class jdkTool(RunEnvTool, JavaToolMixIn):
    """Java Development Kit.

Home: http://openjdk.java.net/

Due to issues with Oracle's licensing, cid
supports only automatic installation of OpenJDK.

jdkVer supports:
- only one digit like 6, 7, 8, 9 (Zulu JDK (http://zulu.org)
- use jdkDir for custom JDK
- jdkVer is equal to javaVer by default
"""
    __slots__ = ()

    def getDeps(self):
        return ['java']

    def envNames(self):
        return ['jdkDir', 'jdkVer']

    def getVersionParts(self):
        return 1

    def _installTool(self, env):
        if env.get('jdkDir', None):
            return

        ver = env['jdkVer']

        # Zulu is installed in javaTool
        # leaving it here for possible future use
        # self._install.deb(['openjdk-{0}-jdk'.format(ver)])
        # self._install.yum(['java-1.{0}.0-openjdk-devel'.format(ver)])
        # self._install.zypper(['java-1_{0}_0-openjdk-devel'.format(ver)])
        self._install.pacman(['jdk{0}-openjdk'.format(ver)])
        self._install.emerge(['=dev-java/oracle-jdk-bin-1.{0}*'.format(ver)])

        if self._detect.isAlpineLinux():
            self._install.apkCommunity()
            self._install.apk('openjdk{0}'.format(ver))
            return

    def uninstallTool(self, env):
        pass

    def initEnv(self, env):
        ospath = self._ospath
        environ = self._environ
        glob = self._ext.glob
        detect = self._detect

        if env.get('jdkDir', None):
            java_home = env['jdkDir']
            bin_dir = ospath.join(java_home, 'bin')

            environ['JAVA_HOME'] = java_home
            environ['JDK_HOME'] = java_home

            self._pathutil.addBinPath(bin_dir, True)

            super(jdkTool, self).initEnv(env, 'javac')
            return

        env.setdefault('jdkVer', env['javaVer'])
        ver = env['jdkVer']

        candidates = [
            # Zulu
            '/usr/lib/jvm/zulu-{0}*/bin/javac'.format(ver),
            # Debian / Ubuntu
            # "/usr/lib/jvm/java-{0}-openjdk*/bin/javac".format(ver),
            # RedHat
            # "/usr/lib/jvm/java-1.{0}.0/bin/javac".format(ver),
            # OpenSuse
            # "/usr/lib*/jvm/java-1.{0}.0/bin/javac".format(ver),
            # Default oracle
            # "/opt/jdk/jdk1.{0}*/bin/javac".format(ver),
        ]

        if detect.isGentoo() or detect.isArchLinux():
            candidates += [
                "/usr/lib/jvm/java-{0}-openjdk*/bin/javac".format(ver),
            ]
        elif detect.isAlpineLinux():
            candidates += [
                "/usr/lib/jvm/java-1.{0}-openjdk/bin/javac".format(ver),
            ]
        elif detect.isMacOS():
            candidates += [
                "/Library/Java/JavaVirtualMachines/zulu-{0}.jdk/Contents/Home/bin/javac".format(
                    ver)
            ]

        for c in candidates:
            if ospath.exists(c):
                bin_name = [c]
            else:
                bin_name = glob.glob(c)

            if bin_name:
                bin_name = bin_name[0]
                bin_dir = ospath.dirname(bin_name)
                java_home = ospath.dirname(bin_dir)

                env['jdkDir'] = java_home
                environ['JAVA_HOME'] = java_home
                environ['JDK_HOME'] = java_home

                self._pathutil.addBinPath(bin_dir, True)
                self._have_tool = True
                break
