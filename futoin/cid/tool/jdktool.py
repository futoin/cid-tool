
import os
import glob

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
        # self._requireDeb(['openjdk-{0}-jdk'.format(ver)])
        # self._requireYum(['java-1.{0}.0-openjdk-devel'.format(ver)])
        # self._requireZypper(['java-1_{0}_0-openjdk-devel'.format(ver)])
        self._requirePacman(['jdk{0}-openjdk'.format(ver)])
        self._requireEmerge(['=dev-java/oracle-jdk-bin-1.{0}*'.format(ver)])

        if self._isAlpineLinux():
            self._requireApkCommunity()
            self._requireApk('openjdk{0}'.format(ver))
            return

    def uninstallTool(self, env):
        pass

    def initEnv(self, env):
        if env.get('jdkDir', None):
            java_home = env['jdkDir']
            bin_dir = os.path.join(java_home, 'bin')

            os.environ['JAVA_HOME'] = java_home
            os.environ['JDK_HOME'] = java_home

            self._addBinPath(bin_dir, True)

            super(jdkTool, self).initEnv(env, 'javac')
            return

        env.setdefault('jdkVer', env['javaVer'])
        ver = env['jdkVer']

        candidates = [
            # Zulu
            '/usr/lib/jvm/zulu-{0}*/bin/javac'.format(ver),
            # Debian / Ubuntu
            #"/usr/lib/jvm/java-{0}-openjdk*/bin/javac".format(ver),
            # RedHat
            #"/usr/lib/jvm/java-1.{0}.0/bin/javac".format(ver),
            # OpenSuse
            #"/usr/lib*/jvm/java-1.{0}.0/bin/javac".format(ver),
            # Default oracle
            #"/opt/jdk/jdk1.{0}*/bin/javac".format(ver),
        ]

        if self._isGentoo() or self._isArchLinux():
            candidates += [
                "/usr/lib/jvm/java-{0}-openjdk*/bin/javac".format(ver),
            ]
        elif self._isAlpineLinux():
            candidates += [
                "/usr/lib/jvm/java-1.{0}-openjdk/bin/javac".format(ver),
            ]
        elif self._isMacOS():
            candidates += [
                "/Library/Java/JavaVirtualMachines/zulu-{0}.jdk/Contents/Home/bin/javac".format(
                    ver)
            ]

        for c in candidates:
            if os.path.exists(c):
                bin_name = [c]
            else:
                bin_name = glob.glob(c)

            if bin_name:
                bin_name = bin_name[0]
                bin_dir = os.path.dirname(bin_name)
                java_home = os.path.dirname(bin_dir)

                env['jdkDir'] = java_home
                os.environ['JAVA_HOME'] = java_home
                os.environ['JDK_HOME'] = java_home

                self._addBinPath(bin_dir, True)
                self._have_tool = True
                break
