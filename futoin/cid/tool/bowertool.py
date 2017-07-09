
from ..buildtool import BuildTool
from .npmtoolmixin import NpmToolMixIn


class bowerTool(NpmToolMixIn, BuildTool):
    """Bower: a package manager for the web.

Home: https://bower.io/
"""
    __slots__ = ()

    BOWER_JSON = 'bower.json'

    def autoDetectFiles(self):
        return self.BOWER_JSON

    def loadConfig(self, config):
        content = self._pathutil.loadJSONConfig(self.BOWER_JSON)
        if content is None:
            return

        f = 'name'
        if f in content and f not in config:
            config[f] = content[f]

    def updateProjectConfig(self, config, updates):
        def updater(json):
            f = 'name'
            if f in updates:
                json[f] = updates[f]

            # version is deprecated
            if 'version' in json:
                del json['version']

        return self._pathutil.updateJSONConfig(self.BOWER_JSON, updater)

    def onPrepare(self, config):
        bowerBin = config['env']['bowerBin']
        self._executil.callExternal([bowerBin, 'install'])

    def onPackage(self, config):
        # Bower does not remove dev deps by itself
        self._pathutil.rmTree('bower_components')

        bowerBin = config['env']['bowerBin']
        self._executil.callExternal([bowerBin, 'install', '--production'])
