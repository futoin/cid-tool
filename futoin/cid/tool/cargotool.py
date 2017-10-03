
from ..buildtool import BuildTool
from ..testtool import TestTool
from ..rmstool import RmsTool


class cargoTool(BuildTool, TestTool, RmsTool):
    """Cargo, Rust;s Package Manager.

Home: http://doc.crates.io/

Build targets:
    prepare -> clean
    build -> build
    check -> test
Override targets with .config.toolTune.

"""
    __slots__ = ()

    def autoDetectFiles(self):
        return 'Cargo.toml'

    def getDeps(self):
        return ['rust']

    def _installTool(self, env):
        if self._detect.isAlpineLinux():
            self._install.apk('cargo')

    def uninstallTool(self, env):
        pass

    def onPrepare(self, config):
        self._executil.callExternal([
            config['env']['cargoBin'], 'clean',
        ])

    def onBuild(self, config):
        args = []

        if not config.get('debugBuild', False):
            args.append('--release')

        self._executil.callExternal(
            [config['env']['cargoBin'], 'build'] + args)

    def onPackage(self, config):
        cmd = [config['env']['cargoBin'], 'package', '--allow-dirty']
        self._executil.callMeaningful(cmd)
        self._pathutil.addPackageFiles(config, 'target/package/*.crate')

    def onCheck(self, config):
        cmd = [config['env']['cargoBin'], 'test']
        self._executil.callMeaningful(cmd)

    def onRunDev(self, config):
        cmd = [config['env']['cargoBin'], 'run']
        self._executil.callMeaningful(cmd)

    def rmsUpload(self, config, rms_pool, package_list):
        cmd = [config['env']['cargoBin'], 'publish']
        self._executil.callMeaningful(cmd)
