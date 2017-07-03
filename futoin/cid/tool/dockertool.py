
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
        repo = env.get('dockerRepos', 'https://download.docker.com')

        if detect.isCentOS():
            self._install.yumRepo(
                'docker', repo + '/linux/centos/docker-ce.repo')

        elif detect.isFedora():
            self._install.yumRepo(
                'docker', repo + '/linux/fedora/docker-ce.repo')

        elif detect.isDebian():
            gpg = self._callCurl(env, [repo + '/linux/debian/gpg'])
            self._install.aptRepo(
                'docker',
                'deb [arch=amd64] {0}/linux/debian $codename$ stable'.format(
                    repo),
                gpg
            )

        elif detect.isUbuntu():
            gpg = self._callCurl(env, [repo + '/linux/ubuntu/gpg'])
            self._install.aptRepo(
                'docker',
                'deb [arch=amd64] {0}/linux/ubuntu $codename$ stable'.format(
                    repo),
                gpg,
                codename_map={
                    'zesty': 'yakkety',
                },
                repo_base=repo,
            )

        elif detect.isOracleLinux() or detect.isRHEL():
            self._install.yumRepo(
                'docker', repo + '/linux/centos/docker-ce.repo')

        # elif detect.isOpenSUSE() or detect.isSLES():
        #    virt_repo = 'https://download.opensuse.org/repositories/Virtualization'
        #
        #    with open('/etc/os-release', 'r') as rf:
        #        releasever = re.search('VERSION="([0-9.]+)"', rf.read()).group(1)
        #
        #
        #    if detect.isOpenSUSE():
        #        virt_repo += '/openSUSE_Leap_'+releasever
        #    else:
        #        virt_repo += '/SLE_'+releasever
        #
        #    virt_gpg = self._callCurl(env, [virt_repo+'/repodata/repomd.xml.key'])
        #    self._install.zypperRepo('Virtualization', virt_repo+'/Virtualization.repo', virt_gpg)
        #
        #    gpg = self._callCurl(env, [repo+'/linux/centos/gpg'])
        #    self._install.zypperRepo('docker', repo + '/linux/centos/7/x86_64/stable/', gpg, yum=True)

        else:
            self._install.yumEPEL()
            self._install.debrpm(['docker'])
            self._install.debrpm(['docker-engine'])
            self._install.emerge(['app-emulation/docker'])
            self._install.pacman(['docker'])
            self._install.apkCommunity()
            self._install.apk(['docker'])

            self._executil.startService('docker')

            return

        ver = env.get('dockerVer', None)

        if ver:
            self._install.debrpm(['docker-ce-' + ver])
        else:
            self._install.debrpm(['docker-ce'])

        self._executil.startService('docker')

    def onBuild(self, config):
        ospath = self._ospath

        env = config['env']
        tag = env.get('dockerTag', ospath.basename(ospath.realpath('.')))
        cmd = [env['dockerBin'], 'build', '-t', tag, '.']

        if self._isDockerAdmin():
            self._executil.callExternal(cmd)
        else:
            sudo = self._pathutil.which('sudo')
            self._executil.callExternal([sudo] + cmd)

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

        if self._isDockerAdmin():
            self._executil.callExternal(cmd)
        else:
            sudo = self._pathutil.which('sudo')
            self._executil.callExternal([sudo] + cmd)

    def _isDockerAdmin(self):
        detect = self._detect
        return detect.haveGroup('docker') or detect.isAdmin()

    def tuneDefaults(self):
        return {
            'minMemory': '256M',
            'debugOverhead': '128M',
            'connMemory': '100K',
            'debugConnOverhead': '1M',
            'socketType': 'tcp',
            'scalable': False,
        }
