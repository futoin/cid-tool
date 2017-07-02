
from ..buildtool import BuildTool


class pipTool(BuildTool):
    """The PyPA recommended tool for installing Python packages.

Home: https://pypi.python.org/pypi/pip
"""
    __slots__ = ()

    REQUIREMENTS_FILE = 'requirements.txt'

    def autoDetectFiles(self):
        return self.REQUIREMENTS_FILE

    def getDeps(self):
        return ['python', 'virtualenv']

    def envNames(self):
        return ['pipBin', 'pipVer']

    def _installTool(self, env):
        ospath = self._ospath

        if ospath.exists(env['pipBin']):
            self.updateTool(env)
        else:
            self._executil.callExternal([
                ospath.join(env['virtualenvDir'], 'bin',
                            'easy_install'), 'pip'
            ])

    def updateTool(self, env):
        self._executil.callExternal([
            env['pipBin'], 'install', '-q',
            '--upgrade',
            'pip>={0}'.format(env['pipVer']),
        ])

    def uninstallTool(self, env):
        pass

    def initEnv(self, env):
        ospath = self._ospath
        pipBin = ospath.join(env['virtualenvDir'], 'bin', 'pip')
        pipBin = env.setdefault('pipBin', pipBin)
        pipVer = env.setdefault('pipVer', '9.0.1')

        if ospath.exists(pipBin):
            pipFactVer = self._executil.callExternal(
                [pipBin, '--version'], verbose=False)
            pipFactVer = [int(v) for v in pipFactVer.split(' ')[1].split('.')]
            pipNeedVer = [int(v) for v in pipVer.split('.')]

            self._have_tool = pipNeedVer <= pipFactVer

    def onPrepare(self, config):
        if self._ospath.exists(self.REQUIREMENTS_FILE):
            self._executil.callExternal(
                [config['env']['pipBin'], 'install', '-r', self.REQUIREMENTS_FILE])
