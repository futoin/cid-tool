
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
        env = config['env']

        # Dirty hack
        #---
        bundlerTools = env.get('bundlerTools', {})
        do_bundler_hack = len(bundlerTools) > 0

        for (k, v) in bundlerTools.items():
            tcmd = [env['bundlerBin'], 'add', k]

            if v:
                tcmd.append('--version={0}'.format(v))

            self._executil.callExternal(tcmd, suppress_fail=True)

        if len(bundlerTools) > 0:
            cmd = [env['bundlerBin'], 'install']
            self._executil.callExternal(cmd)

        # Main install
        #---
        cmd = [env['bundlerBin'], 'install']

        if self._ospath.exists('Gemfile.lock'):
            cmd.append('--deployment')

        self._executil.callMeaningful(cmd)

    def onPackage(self, config):
        cmd = [config['env']['bundlerBin'], 'install',
               '--deployment', '--clean']
        self._executil.callMeaningful(cmd)
