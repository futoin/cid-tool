
import re
import os

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

    def autoDetectFiles(self):
        return 'Dockerfile'

    def getOrder(self):
        return 10

    def envNames(self):
        return ['dockerBin', 'dockerVer', 'dockerRepos', 'dockerTag']

    def _installTool(self, env):
        repo = env.get('dockerRepos', 'https://download.docker.com')

        if self._isCentOS():
            self._addYumRepo('docker', repo + '/linux/centos/docker-ce.repo')

        elif self._isFedora():
            self._addYumRepo('docker', repo + '/linux/fedora/docker-ce.repo')

        elif self._isDebian():
            gpg = self._callCurl(env, [repo + '/linux/debian/gpg'])
            self._addAptRepo(
                'docker',
                'deb [arch=amd64] {0}/linux/debian $codename$ stable'.format(
                    repo),
                gpg
            )

        elif self._isUbuntu():
            gpg = self._callCurl(env, [repo + '/linux/ubuntu/gpg'])
            self._addAptRepo(
                'docker',
                'deb [arch=amd64] {0}/linux/ubuntu $codename$ stable'.format(
                    repo),
                gpg,
                codename_map={
                    'zesty': 'yakkety',
                },
                repo_base=repo,
            )

        elif self._isOracleLinux() or self._isRHEL():
            self._addYumRepo('docker', repo + '/linux/centos/docker-ce.repo')

        # elif self._isOpenSUSE() or self._isSLES():
        #    virt_repo = 'https://download.opensuse.org/repositories/Virtualization'
        #
        #    with open('/etc/os-release', 'r') as rf:
        #        releasever = re.search('VERSION="([0-9.]+)"', rf.read()).group(1)
        #
        #
        #    if self._isOpenSUSE():
        #        virt_repo += '/openSUSE_Leap_'+releasever
        #    else:
        #        virt_repo += '/SLE_'+releasever
        #
        #    virt_gpg = self._callCurl(env, [virt_repo+'/repodata/repomd.xml.key'])
        #    self._addZypperRepo('Virtualization', virt_repo+'/Virtualization.repo', virt_gpg)
        #
        #    gpg = self._callCurl(env, [repo+'/linux/centos/gpg'])
        #    self._addZypperRepo('docker', repo + '/linux/centos/7/x86_64/stable/', gpg, yum=True)

        else:
            self._requireYumEPEL()
            self._requirePackages(['docker'])
            self._requirePackages(['docker-engine'])
            self._requireEmerge(['app-emulation/docker'])
            self._requirePacman(['docker'])
            self._requireApkCommunity()
            self._requireApk(['docker'])

            self._startService('docker')

            return

        ver = env.get('dockerVer', None)

        if ver:
            self._requirePackages(['docker-ce-' + ver])
        else:
            self._requirePackages(['docker-ce'])

        self._startService('docker')

    def onBuild(self, config):
        env = config['env']
        tag = env.get('dockerTag', os.path.basename(os.path.realpath('.')))
        cmd = [env['dockerBin'], 'build', '-t', tag, '.']

        if self._haveGroup('docker') or self._isAdmin():
            self._callExternal(cmd)
        else:
            sudo = self._which('sudo')
            self._callExternal([sudo] + cmd)

    def onExec(self, env, args, replace=True):
        bin = env['dockerBin']

        if self._haveGroup('docker') or self._isAdmin():
            cmd = [bin] + args
        else:
            sudo = self._which('sudo')
            cmd = [sudo, bin] + args

        self._callInteractive(cmd, replace=replace)

    def onRun(self, config, svc, args):
        env = config['env']
        cmd = [env['dockerBin'], 'run', svc['path']]

        if self._haveGroup('docker') or self._isAdmin():
            self._callExternal(cmd)
        else:
            sudo = self._which('sudo')
            self._callExternal([sudo] + cmd)

    def tuneDefaults(self):
        return {
            'minMemory': '256M',
            'debugOverhead': '128M',
            'connMemory': '100K',
            'debugConnOverhead': '1M',
            'socketType': 'tcp',
            'scalable': False,
        }
