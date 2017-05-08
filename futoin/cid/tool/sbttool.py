
from ..buildtool import BuildTool
from ..testtool import TestTool
from .sdkmantoolmixin import SdkmanToolMixIn


class sbtTool(SdkmanToolMixIn, BuildTool, TestTool):
    """The interactive build tool (Scala).

Home: http://www.scala-sbt.org/

Installed via SDKMan!

First run of SBT may consume a lot of time on post-installation steps.

Build targets:
    prepare -> clean
    build -> compile
    package -> package
    check -> test
Override targets with .config.toolTune.

Requires Java >= 8.
"""
    _MIN_JAVA = '8'

    def autoDetectFiles(self):
        return 'build.sbt'

    def onPrepare(self, config):
        target = self._getTune(config, 'prepare', 'clean')
        self._callExternal([config['env']['sbtBin'], target])

    def onBuild(self, config):
        target = self._getTune(config, 'build', 'compile')
        self._callExternal([config['env']['sbtBin'], target])

    def onPackage(self, config):
        target = self._getTune(config, 'package', 'package')
        self._callExternal([config['env']['sbtBin'], target])
        self._addPackageFiles(config, 'target/scala-*/*.jar')

    def onRunDev(self, config):
        target = self._getTune(config, 'run', 'check')
        self._callExternal([config['env']['sbtBin'], target])

    def onCheck(self, config):
        target = self._getTune(config, 'check', 'test')
        self._callExternal([config['env']['sbtBin'], target])
