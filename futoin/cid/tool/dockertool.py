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
from ..runenvtool import RunEnvTool
from ..runtimetool import RuntimeTool
from .curltoolmixin import CurlToolMixIn


class dockerTool(BuildTool, CurlToolMixIn, RunEnvTool, RuntimeTool):
    """Docker - Build, Ship, and Run Any App, Anywhere.

Home: https://www.docker.com/

Experimental support.

Docker CE support is added for CentOS, Fedora, Debian and Ubuntu.
For other systems, "docker" or "docker-engine" packages is tried to be installed.

Docker EE or other installation methods are out of scope for now.
"""
    __slots__ = ()

    def autoDetectFiles(self):
        return 'Dockerfile'

    def getOrder(self):
        return 10

    def envNames(self):
        return ['dockerBin', 'dockerVer', 'dockerRepos', 'dockerTag']

    def _installTool(self, env):
        detect = self._detect
        install = self._install
        repo = env.get('dockerRepos', 'https://download.docker.com')

        if detect.isCentOS():
            install.yumRepo(
                'docker', repo + '/linux/centos/docker-ce.repo')

        elif detect.isFedora():
            install.yumRepo(
                'docker', repo + '/linux/fedora/docker-ce.repo')

        elif detect.isDebian():
            gpg = self._callCurl(env, [repo + '/linux/debian/gpg'])
            install.aptRepo(
                'docker',
                'deb [arch=amd64] {0}/linux/debian $codename$ stable'.format(
                    repo),
                gpg
            )

        elif detect.isUbuntu():
            gpg = self._callCurl(env, [repo + '/linux/ubuntu/gpg'])
            install.aptRepo(
                'docker',
                'deb [arch=amd64] {0}/linux/ubuntu $codename$ stable'.format(
                    repo),
                gpg,
                codename_map={},
                repo_base=repo,
            )

        elif detect.isRHEL():
            install.yumRHELRepo('server-extras-rpms')
            install.yum(['docker'])
            self._executil.startService('docker')
            return

        elif detect.isOracleLinux():
            install.yumOLPublic('addons')
            install.yum(['docker'])
            self._executil.startService('docker')
            return

        elif detect.isSLES():
            install.SUSEConnectVerArch('sle-module-containers')
            install.zypper('docker')
            self._executil.startService('docker')
            return

        else:
            install.yumEPEL()
            install.debrpm(['docker'])
            install.debrpm(['docker-engine'])
            install.emerge(['app-emulation/docker'])
            install.pacman(['docker'])
            install.apkCommunity()
            install.apk(['docker'])

            self._executil.startService('docker')

            return

        ver = env.get('dockerVer', None)

        if ver:
            install.debrpm(['docker-ce-' + ver])
        else:
            install.debrpm(['docker-ce'])

        self._executil.startService('docker')

    def onBuild(self, config):
        ospath = self._ospath

        env = config['env']
        tag = env.get('dockerTag', ospath.basename(ospath.realpath('.')))
        cmd = [env['dockerBin'], 'build', '-t', tag, '.']

        if not self._isDockerAdmin():
            sudo = self._pathutil.which('sudo')
            cmd = [sudo] + cmd

        self._executil.callMeaningful(cmd)

    def onExec(self, env, args, replace=True):
        bin = env['dockerBin']

        if self._isDockerAdmin():
            cmd = [bin] + args
        else:
            sudo = self._pathutil.which('sudo')
            cmd = [sudo, bin] + args

        self._executil.callInteractive(cmd, replace=replace)

    def onRun(self, config, svc, args):
        env = config['env']
        cmd = [env['dockerBin'], 'run', svc['path']]

        if not self._isDockerAdmin():
            sudo = self._pathutil.which('sudo')
            cmd = [sudo] + cmd

        self._executil.callMeaningful(cmd)

    def _isDockerAdmin(self):
        detect = self._detect
        return detect.haveGroup('docker') or detect.isAdmin()

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
