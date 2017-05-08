
import os

from ..buildtool import BuildTool
from .gemtoolmixin import GemToolMixIn


class puppetTool(GemToolMixIn, BuildTool):
    """Puppet system automation.

Home: https://puppet.com/

Primary purpose is to support Puppet module development.
"""
    METADATA_FILE = 'metadata.json'

    def envNames(self):
        return ['puppetVer', 'puppetBin']

    def initEnv(self, env):
        super(puppetTool, self).initEnv(env)
        puppet_ver = env.setdefault('puppetVer', None)

        if self._have_tool and puppet_ver:
            try:
                found_ver = self._callExternal(
                    [env['puppetBin'], '--version'], verbose=False)
                self._have_tool = found_ver.find(puppet_ver) >= 0
            except:
                self._have_tool = False
                del env['puppetBin']

    def autoDetectFiles(self):
        return self.METADATA_FILE

    def loadConfig(self, config):
        content = self._loadJSONConfig(self.METADATA_FILE)
        if content is None:
            return

        for f in ('name', 'version'):
            if f in content and f not in config:
                config[f] = content[f]

        config['package'] = 'pkg'

    def updateProjectConfig(self, config, updates):
        def updater(json):
            for f in ('name', 'version'):
                if f in updates:
                    json[f] = updates[f]

        return self._updateJSONConfig(self.METADATA_FILE, updater)

    def onPrepare(self, config):
        if os.path.exists('pkg'):
            self._rmTree('pkg')

    def onBuild(self, config):
        puppetBin = config['env']['puppetBin']
        self._callExternal([puppetBin, 'module', 'build'])

    def onPackage(self, config):
        package_file = 'pkg/{0}-{1}.tar.gz'.format(
            config['name'],
            config['version']
        )

        if not os.path.exists(package_file):
            self._errorExit(
                'Puppet Module built package is missing: ' + package_file)

        self._addPackageFiles(config, package_file)
