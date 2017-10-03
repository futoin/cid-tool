
from ..buildtool import BuildTool
from .gemtoolmixin import GemToolMixIn


class bundlerTool(GemToolMixIn, BuildTool):
    """Bundler: The best way to manage a Ruby application's gems.

Home: http://bundler.io/
"""
    __slots__ = ()

    def autoDetectFiles(self):
        return 'Gemfile'

    def initEnv(self, env):
        super(bundlerTool, self).initEnv(env, 'bundle')

    def onPrepare(self, config):
        cmd = [config['env']['bundlerBin'], 'install']
        self._executil.callMeaningful(cmd)

    def onPackage(self, config):
        cmd = [config['env']['bundlerBin'], 'install',
               '--deployment', '--clean']
        self._executil.callMeaningful(cmd)
