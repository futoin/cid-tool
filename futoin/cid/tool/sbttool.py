
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
    __slots__ = ()

    def _minJava(self):
        return '8'

    def autoDetectFiles(self):
        return 'build.sbt'

    def _callSBT(self, config, target):
        cmd = [config['env']['sbtBin'], target]
        self._executil.callMeaningful(cmd)

    def onPrepare(self, config):
        target = self._getTune(config, 'prepare', 'clean')
        self._callSBT(config, target)

    def onBuild(self, config):
        target = self._getTune(config, 'build', 'compile')
        self._callSBT(config, target)

    def onPackage(self, config):
        target = self._getTune(config, 'package', 'package')
        self._callSBT(config, target)
        self._pathutil.addPackageFiles(config, 'target/scala-*/*.jar')

    def onRunDev(self, config):
        target = self._getTune(config, 'run', 'check')
        self._callSBT(config, target)

    def onCheck(self, config):
        target = self._getTune(config, 'check', 'test')
        self._callSBT(config, target)
