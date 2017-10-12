
from ..buildtool import BuildTool
from .gemtoolmixin import GemToolMixIn


class bundlerTool(GemToolMixIn, BuildTool):
    """Bundler: The best way to manage a Ruby application's gems.

Home: http://bundler.io/

Note:
1. It will use per-project BUNDLE_PATH=vendor/bundle by default
2. In deployment with missing vendor/bundle, it uses per-deployment BUNDLE_PATH
3. If run outside of project/deployment, standard ~/.bundle is used
"""
    __slots__ = ()

    def envNames(self):
        return ['bundlePath', 'bundlerVer']

    def autoDetectFiles(self):
        return 'Gemfile'

    def initEnv(self, env):
        ospath = self._ospath

        if 'CID_DEPLOY_HOME' in self._environ:
            if ospath.exists('vendor/bundle'):
                # packed deps
                bundlePath = self._ospath.realpath('vendor/bundle')
            else:
                # per deployment
                bundlePath = ospath.join(
                    self._pathutil.deployHome(), '.bundle')
        elif not ospath.exists('Gemfile'):
            # global
            bundlePath = ospath.join(self._pathutil.deployHome(), '.bundle')
        else:
            # per project
            bundlePath = self._ospath.realpath('vendor/bundle')

        bundlePath = env.setdefault('bundlePath', bundlePath)
        self._environ['BUNDLE_PATH'] = bundlePath

        super(bundlerTool, self).initEnv(env, 'bundle')

    def onPrepare(self, config):
        cmd = [config['env']['bundlerBin'], 'install', '--quiet']

        if self._ospath.exists('Gemfile.lock'):
            cmd.append('--deployment')

        self._executil.callMeaningful(cmd)

    def onPackage(self, config):
        cmd = [config['env']['bundlerBin'], 'install', '--quiet',
               '--deployment', '--clean']
        self._executil.callMeaningful(cmd)
