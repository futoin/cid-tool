
import os

from ..buildtool import BuildTool
from ..rmstool import RmsTool


class npmTool(BuildTool, RmsTool):
    """npm is the package manager for JavaScript.

Home: https://www.npmjs.com/

In RMS mode support tuning through .toolTune.npm:
    .tag - npm publish --tag
    .access - npm publish --access
"""
    PACKAGE_JSON = 'package.json'

    def autoDetectFiles(self):
        return self.PACKAGE_JSON

    def getDeps(self):
        return ['node']

    def _installTool(self, env):
        if self._isAlpineLinux():
            if env['nodeVer'] == 'current':
                self._requireApk('nodejs-npm-current')
            else:
                self._requireApk('nodejs-npm')
            return

    def updateTool(self, env):
        if self._isAlpineLinux():
            return

        self._callExternal([env['npmBin'], 'update', '-g', 'npm'])

    def uninstallTool(self, env):
        pass

    def loadConfig(self, config):
        content = self._loadJSONConfig(self.PACKAGE_JSON)
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

        return self._updateJSONConfig(self.PACKAGE_JSON, updater)

    def onPrepare(self, config):
        if os.path.exists(self.PACKAGE_JSON):
            npmBin = config['env']['npmBin']
            self._callExternal([npmBin, 'install'])

    def onPackage(self, config):
        if os.path.exists(self.PACKAGE_JSON):
            npmBin = config['env']['npmBin']
            self._callExternal([npmBin, 'prune', '--production'])

    def rmsUpload(self, config, rms_pool, package_list):
        npmBin = config['env']['npmBin']
        cmd = [npmBin, 'publish']

        tune = config.get('toolTune', {}).get('npm', {})

        if 'tag' in tune:
            cmd += ['--tag', tune['tag']]

        if 'access' in tune:
            cmd += ['--access', tune['access']]

        self._callExternal(cmd)

    def rmsPoolList(self, config):
        return [
            'registry',
        ]
