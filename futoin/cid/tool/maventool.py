#
# Copyright 2015-2017 (c) Andrey Galkin
#


from ..buildtool import BuildTool
from ..testtool import TestTool
from .sdkmantoolmixin import SdkmanToolMixIn


class mavenTool(SdkmanToolMixIn, BuildTool, TestTool):
    """Apache Maven is a software project management and comprehension tool.

Home: https://maven.apache.org/

Expects clean, compile, package and test targets.

Build targets:
    prepare -> clean
    build -> compile
    package -> package
    check -> test
Override targets with .config.toolTune.

Requires Java >= 7.
"""
    __slots__ = ()

    def _minJava(self):
        return '7'

    def autoDetectFiles(self):
        return 'pom.xml'

    def _binName(self):
        return 'mvn'

    def _callMaven(self, config, target):
        cmd = [config['env']['mavenBin'], target]
        self._executil.callMeaningful(cmd)

    def onPrepare(self, config):
        target = self._getTune(config, 'prepare', 'clean')
        self._callMaven(config, target)

    def onBuild(self, config):
        target = self._getTune(config, 'build', 'compile')
        self._callMaven(config, target)

    def onPackage(self, config):
        target = self._getTune(config, 'package', 'package')
        self._callMaven(config, target)
        self._pathutil.addPackageFiles(config, 'target/*.jar')

    def onCheck(self, config):
        target = self._getTune(config, 'check', 'test')
        self._callMaven(config, target)
