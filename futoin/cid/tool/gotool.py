from ..runtimetool import RuntimeTool
from .bashtoolmixin import BashToolMixIn


class goTool(BashToolMixIn, RuntimeTool):
    """The Go Programming Language

Home: https://golang.org/

All versions are installed through GVM.

Only binary releases of Golang are supported for installation
through CID, but you can install source releases through
"cid tool exec gvm -- install sourcetag".
"""

    def getDeps(self):
        return ['gvm', 'bash', 'binutils', 'gcc']

    def _installTool(self, env):
        if self._isAlpineLinux():
            self._requireApkCommunity()
            self._requireApk('go')
            return

        # in case GVM is already installed without these deps
        self._requireDeb(['bison', 'build-essential'])
        self._requireRpm(['bison', 'glibc-devel'])
        self._requireEmergeDepsOnly(['dev-lang/go'])
        self._requirePacman(['bison', 'glibc', ])
        self._requireApk('bison')
        self._requireBuildEssential()

        self._callBash(env,
                       'source {0} && gvm install {1} --binary'
                       .format(env['gvmInit'], env['goVer'])
                       )

    def updateTool(self, env):
        self._installTool(env)

    def uninstallTool(self, env):
        self._callBash(env,
                       'source {0} && gvm uninstall {1}'
                       .format(env['gvmInit'], env['goVer'])
                       )
        self._have_tool = False

    def envNames(self):
        return ['goVer', 'goBin']

    def initEnv(self, env):
        if self._isAlpineLinux():
            super(goTool, self).initEnv(env)
            return

        if not env.get('goVer', None):
            try:
                cmd = 'source {0} && gvm listall'.format(env['gvmInit'])
                ver_list = self._callBash(env, cmd, verbose=False)
                ver_list = ver_list.split("\n")

                import re
                rex = re.compile('^go[0-9]+\.[0-9]+(\.[0-9]+)?$')

                ver_list = [v.strip() for v in ver_list]
                ver_list = filter(lambda x: x and rex.match(x), ver_list)

                env['goVer'] = self._getLatest(list(ver_list))
            except Exception as e:
                self._warn(str(e))
                return

        ver = env['goVer']

        try:
            env_to_set = self._callBash(env,
                                        'source {0} && \
                gvm use {1} >/dev/null && \
                env | egrep -i "(gvm|golang)"'.format(env['gvmInit'], ver),
                                        verbose=False
                                        )
        except:
            return

        if env_to_set:
            self._updateEnvFromOutput(env_to_set)
            super(goTool, self).initEnv(env)

    def onRun(self, config, svc, args):
        env = config['env']
        self._callInteractive([
            env[self._name + 'Bin'], 'run', svc['path']
        ] + args)
