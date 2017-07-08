
from ..buildtool import BuildTool
from .npmtoolmixin import NpmToolMixIn


class yarnTool(NpmToolMixIn, BuildTool):
    """YARN: fast, reliable, and secure dependency management.

Home: https://yarnpkg.com

Note: auto-detected only if yarn.lock is present
"""
    __slots__ = ()

    def autoDetectFiles(self):
        return 'yarn.lock'

    def onPrepare(self, config):
        yarnBin = config['env']['yarnBin']
        self._executil.callExternal([yarnBin, 'install'])

    def onPackage(self, config):
        yarnBin = config['env']['yarnBin']
        self._executil.callExternal([yarnBin, 'install', '--production'])
