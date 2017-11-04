#
# Copyright 2015-2017 (c) Andrey Galkin
#


from ..buildtool import BuildTool


class makeTool(BuildTool):
    """GNU Make.

Home: https://www.gnu.org/software/make/

Expects presence of "clean" target.
Build uses the default target.
"""
    __slots__ = ()

    def autoDetectFiles(self):
        return [
            'GNUmakefile',
            'makefile',
            'Makefile',
        ]

    def _installTool(self, env):
        self._install.debrpm(['make'])
        self._install.emerge(['sys-devel/make'])
        self._install.pacman(['make'])
        self._install.apk(['make'])

    def onPrepare(self, config):
        cmd = [config['env']['makeBin'], 'clean']
        self._executil.callMeaningful(cmd)

    def onBuild(self, config):
        target = self._getTune(config, 'build')

        if target:
            args = [target]
        else:
            args = []

        cmd = [config['env']['makeBin']] + args
        self._executil.callMeaningful(cmd)
