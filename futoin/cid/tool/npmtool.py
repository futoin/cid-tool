
from ..buildtool import BuildTool
from ..rmstool import RmsTool


class npmTool(BuildTool, RmsTool):
    """npm is the package manager for JavaScript.

Home: https://www.npmjs.com/

In RMS mode support tuning through .toolTune.npm:
    .tag - npm publish --tag
    .access - npm publish --access

Note: it auto-disables, if Yarn tool is detected
"""
    __slots__ = ()

    PACKAGE_JSON = 'package.json'

    def autoDetectFiles(self):
        return self.PACKAGE_JSON

    def getDeps(self):
        return ['node']

    def _isGlobalNpm(self):
        return self._detect.isAlpineLinux()

    def _isYarnInUse(self, config):
        return 'yarn' in config['toolOrder']

    def _installTool(self, env):
        if self._isGlobalNpm():
            if env['nodeVer'] == 'current':
                self._install.apk('nodejs-npm-current')
            else:
                self._install.apk('nodejs-npm')
            return

    def updateTool(self, env):
        if self._isGlobalNpm():
            return

        self._executil.callExternal([env['npmBin'], 'update', '-g', 'npm'])

    def uninstallTool(self, env):
        pass

    def loadConfig(self, config):
        content = self._pathutil.loadJSONConfig(self.PACKAGE_JSON)
        if content is None:
            return

        for f in ('name', 'version'):
            if f in content and f not in config:
                config[f] = content[f]

    def updateProjectConfig(self, config, updates):
        def updater(json):
            for f in ('name', 'version'):
                if f in updates:
                    json[f] = updates[f]

        return self._pathutil.updateJSONConfig(self.PACKAGE_JSON, updater)

    def onPrepare(self, config):
        if self._ospath.exists(self.PACKAGE_JSON) and not self._isYarnInUse(config):
            npmBin = config['env']['npmBin']
            self._executil.callExternal([npmBin, 'install'])

    def onPackage(self, config):
        npmBin = config['env']['npmBin']

        if self._ospath.exists(self.PACKAGE_JSON) and not self._isYarnInUse(config):
            self._executil.callExternal([npmBin, 'prune', '--production'])

        if config.get('rms', None) == self._name:
            self._executil.callExternal([npmBin, 'pack'])
            package = '{0}-{1}.tgz'.format(
                config['name'], config['version'])
            self._pathutil.addPackageFiles(config, package)

    def rmsUpload(self, config, rms_pool, package_list):
        npmBin = config['env']['npmBin']
        cmd = [npmBin, 'publish']

        tune = config.get('toolTune', {}).get('npm', {})

        if 'tag' in tune:
            cmd += ['--tag', tune['tag']]

        if 'access' in tune:
            cmd += ['--access', tune['access']]

        self._executil.callExternal(cmd)

    def rmsPoolList(self, config):
        return [
            'registry',
        ]
