
from ..runenvtool import RunEnvTool
from .bashtoolmixin import BashToolMixIn
from .curltoolmixin import CurlToolMixIn


class gvmTool(BashToolMixIn, CurlToolMixIn, RunEnvTool):
    """Go Version Manager.

Home: https://github.com/moovweb/gvm
"""
    __slots__ = ()

    GVM_VERSION_DEFAULT = 'master'
    GVM_INSTALLER_DEFAULT = 'https://raw.githubusercontent.com/moovweb/gvm/master/binscripts/gvm-installer'

    def getDeps(self):
        return (
            ['git', 'hg', 'make', 'binutils'] +
            BashToolMixIn.getDeps(self) +
            CurlToolMixIn.getDeps(self))

    def _installTool(self, env):
        self._requireDeb(['bison', 'gcc', 'build-essential'])
        self._requireRpm(['bison', 'gcc', 'glibc-devel'])
        self._requireEmergeDepsOnly(['dev-lang/go'])
        self._requirePacman(['bison', 'gcc', 'glibc', ])
        self._requireApk('bison')
        self._requireBuildEssential()

        gvm_installer = self._callCurl(env, [env['gvmInstaller']])
        self._callBash(
            env,
            input=gvm_installer,
            suppress_fail=True)  # error when Go is not yet installed

    def updateTool(self, env):
        self._installTool(env)

    def uninstallTool(self, env):
        gvm_dir = env['gvmDir']

        if self._ospath.exists(gvm_dir):
            self._rmTree(gvm_dir)

        self._have_tool = False

    def envNames(self):
        return ['gvmDir', 'gvmInstaller']

    def initEnv(self, env):
        ospath = self._ospath
        os = self._os
        environ = self._environ
        gvm_dir = ospath.join(environ['HOME'], '.gvm')
        gvm_dir = env.setdefault('gvmDir', gvm_dir)
        environ['GVM_DEST'] = ospath.dirname(gvm_dir)
        environ['GVM_NAME'] = ospath.basename(gvm_dir)
        environ['GVM_NO_UPDATE_PROFILE'] = '1'

        env.setdefault('gvmVer', self.GVM_VERSION_DEFAULT)
        env.setdefault('gvmInstaller', self.GVM_INSTALLER_DEFAULT)

        env_init = ospath.join(gvm_dir, 'scripts', 'gvm')
        env['gvmInit'] = env_init

        self._have_tool = ospath.exists(env_init)

    def onExec(self, env, args, replace=True):
        cmd = '. {0} && gvm {1}'.format(
            env['gvmInit'], self._ext.subprocess.list2cmdline(args))
        self._callBashInteractive(env, cmd, replace=replace)
