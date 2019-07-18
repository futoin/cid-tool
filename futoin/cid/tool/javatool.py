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
from .javatoolmixin import JavaToolMixIn


class javaTool(RuntimeTool, JavaToolMixIn):
    """Java Runtime Environment.

Home: http://openjdk.java.net/

Due to issues with Oracle's licensing, cid
supports only automatic installation of OpenJDK.

javaVer supports:
- only one digit like 6, 7, 8, 9 (Zulu JDK (http://zulu.org)
- use javaBin for custom JRE
"""
    __slots__ = ()

    def envNames(self):
        return ['javaBin', 'javaVer']

    def getVersionParts(self):
        return 1

    def _installTool(self, env):
        if env.get('javaBin', None):
            return

        detect = self._detect
        install = self._install
        ver = env['javaVer']

        if detect.isMacOS():
            install.brewTap('caskroom/versions')
            pkg_ver = 'zulu{0}'.format(ver)

            if len(install.brewSearch(pkg_ver, True)) > 0:
                install.brew(pkg_ver, True)
            else:
                install.brew('zulu', True)

            return

        if detect.isAlpineLinux():
            install.apkCommunity()
            install.apk('openjdk{0}-jre'.format(ver))
            return

        install.aptRepo(
            'zulu', 'deb http://repos.azulsystems.com/debian stable main', self._ZULU_GPG_KEY)
        install.yumRepo('zulu', 'http://repos.azulsystems.com/rhel/zulu.repo',
                        self._ZULU_GPG_KEY, releasevermax=7)
        install.zypperRepo(
            'zulu', 'http://repos.azulsystems.com/sles/latest', self._ZULU_GPG_KEY)

        # leaving here for possible future use
        # install.deb(['openjdk-{0}-jre-headless'.format(ver)])
        # install.yum(['java-1.{0}.0-openjdk'.format(ver)])
        # install.zypper(['java-1_{0}_0-openjdk'.format(ver)])
        install.debrpm(['zulu-{0}'.format(ver)])

        install.pacman(['jre{0}-openjdk'.format(ver)])
        install.emerge(['=dev-java/oracle-jre-bin-1.{0}*'.format(ver)])

    def uninstallTool(self, env):
        pass

    def initEnv(self, env):
        ospath = self._ospath
        environ = self._environ
        glob = self._ext.glob
        detect = self._detect

        if env.get('javaBin', None):
            bin_dir = ospath.dirname(env['javaBin'])
            java_home = ospath.dirname(bin_dir)

            environ['JAVA_HOME'] = java_home
            environ['JRE_HOME'] = java_home
            self._pathutil.addBinPath(bin_dir, True)

            super(javaTool, self).initEnv(env, 'java')
            return

        ver = env.setdefault('javaVer', self._LATEST_JAVA)

        candidates = [
            # Zulu
            '/usr/lib/jvm/zulu-{0}*/jre/bin/java'.format(ver),
            '/usr/lib/jvm/zulu-{0}*/bin/java'.format(ver),
            # Debian / Ubuntu
            # "/usr/lib/jvm/java-{0}-openjdk*/jre/bin/java".format(ver),
            # RedHat
            # "/usr/lib/jvm/jre-1.{0}.0/bin/java".format(ver),
            # OpenSuse
            # "/usr/lib*/jvm/jre-1.{0}.0/bin/java".format(ver),
            # Default oracle
            # "/opt/jdk/jdk1.{0}*/bin/java".format(ver),
        ]

        if detect.isGentoo() or detect.isArchLinux():
            candidates += [
                "/usr/lib/jvm/java-{0}-openjdk*/jre/bin/java".format(ver),
            ]
        elif detect.isAlpineLinux():
            candidates += [
                "/usr/lib/jvm/java-1.{0}-openjdk/jre/bin/java".format(ver),
            ]
        elif detect.isMacOS():
            candidates += [
                "/Library/Java/JavaVirtualMachines/zulu-{0}.jdk/Contents/Home/jre/bin/java".format(
                    ver),
                "/Library/Java/JavaVirtualMachines/zulu-{0}.jdk/Contents/Home/bin/java".format(
                    ver),
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

                env['javaBin'] = bin_name
                environ['JAVA_HOME'] = java_home
                environ['JRE_HOME'] = java_home
                self._pathutil.addBinPath(bin_dir, True)
                self._have_tool = True
                break

    def onRun(self, config, svc, args):
        env = config['env']
        self._executil.callInteractive([
            env[self._name + 'Bin'], '-jar', svc['path']
        ] + args)

    _ZULU_GPG_KEY = '''
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1

mQINBFNgFa8BEADTL/REB10M+TfiZOtFHqL5LHKkzTMn/O2r5iIqXGhi6iwZazFs
9S5g1eU7WMen5Xp9AREs+OvaHx91onPZ7ZiP7VpZ6ZdwWrnVk1Y/HfI59tWxmNYW
DmKYBGMj4EUpFPSE9EnFj7dm1WdlCvpognCwZQl9D3BseGqN7OLHfwqqmOlbYN9h
HYkT+CaqOoWDIGMB3UkBlMr0GuujEP8N1gxg7EOcSCsZH5aKtXubdUlVSphfAAwD
z4MviB39J22sPBnKmaOT3TUTO5vGeKtC9BAvtgA82jY2TtCEjetnfK/qtzj/6j2N
xVUbHQydwNQVRU92A7334YvCbn3xUUNI0WOscdmfpgCU0Z9Gb2IqDb9cMjgUi8F6
MG/QY9/CZjX62XrHRPm3aXsCJOVh/PO1sl2A/rvv8AkpJKYyhm6T8OBFptCsA3V4
Oic7ZyYhqV0u2r4NON+1MoUeuuoeY2tIrbRxe3ffVOxPzrESzSbc8LC2tYaP+wGd
W0f57/CoDkUzlvpReCUI1Bv5zP4/jhC63Rh6lffvSf2tQLwOsf5ivPhUtwUfOQjg
v9P8Wc8K7XZpSOMnDZuDe9wuvB/DiH/P5yiTs2RGsbDdRh5iPfwbtf2+IX6h2lNZ
XiDKt9Gc26uzeJRx/c7+sLunxq6DLIYvrsEipVI9frHIHV6fFTmqMJY6SwARAQAB
tEdBenVsIFN5c3RlbXMsIEluYy4gKFBhY2thZ2Ugc2lnbmluZyBrZXkuKSA8cGtp
LXNpZ25pbmdAYXp1bHN5c3RlbXMuY29tPokCOAQTAQIAIgUCU2AVrwIbAwYLCQgH
AwIGFQgCCQoLBBYCAwECHgECF4AACgkQsZmDYSGb2cnJ8xAAz1V1PJnfOyaRIP2N
Ho2uRwGdPsA4eFMXb4Z08eGjDMD3b9WW3D0XnCLbJpaZ6klz0W0s2tcYSneTBaSs
RAqxgJgBZ5ZMXtrrHld/5qFoBbStLZLefmcPhnfvamwHDCTLUex8NIAI1u3e9Rhb
5fbH+gpuYpwHX7hz0FOfpn1sxR03UyxU+ey4AdKe9LG3TJVnB0WcgxpobpbqweLH
yzcEQCNoFV3r1rlE13Y0aE31/9apoEwiYvqAzEmE38TukDLl/Qg8rkR1t0/lok2P
G6pWqdN7pmoUovBTvDi5YOthcjZcdOTXXn2Yw4RZVF9uhRsVfku1Eg25SnOje3uY
smtQLME4eESbePdjyV/okCIle66uHZse+7gNyNmWpf01hM+VmAySIAyKa0Ku8AXZ
MydEcJTebrNfW9uMLsBx3Ts7z/CBfRng6F8louJGlZtlSwddTkZVcb26T20xeo0a
ZvdFXM2djTi/a5nbBoZQL85AEeV7HaphFLdPrgmMtS8sSZUEVvdaxp7WJsVuF9cO
Nxsvx40OYTvfco0W41Lm8/sEuQ7YueEVpZxiv5kX56GTU9vXaOOi+8Z7Ee2w6Adz
4hrGZkzztggs4tM9geNYnd0XCdZ/ICAskKJABg7biDD1PhEBrqCIqSE3U497vibQ
Mpkkl/Zpp0BirhGWNyTg8K4JrsQ=
=d320
-----END PGP PUBLIC KEY BLOCK-----
'''

    def tuneDefaults(self, env):
        return {
            'minMemory': '64M',
            'debugOverhead': '128M',
            'connMemory': '100K',
            'debugConnOverhead': '1M',
            'socketType': 'tcp',
            'scalable': False,
            'reloadable': False,
            'multiCore': True,
        }
