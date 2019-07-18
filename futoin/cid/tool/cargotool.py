#
# Copyright 2015-2019 Andrey Galkin <andrey@futoin.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

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
