
from ..buildtool import BuildTool
from .npmtoolmixin import NpmToolMixIn


class webpackTool(NpmToolMixIn, BuildTool):
    """webpack is a module bundler (JS world)

Home: https://webpack.js.org
"""
    __slots__ = ()

    def autoDetectFiles(self):
        return 'webpack.config.js'

    def onBuild(self, config):
        webpackBin = config['env']['webpackBin']
        self._executil.callExternal([
            webpackBin, '-p', '--profile', '--display', '--verbose'])
