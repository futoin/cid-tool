
from ..buildtool import BuildTool


class makeTool(BuildTool):
    """GNU Make.

Home: https://www.gnu.org/software/make/

Expects presence of "clean" target.
Build uses the default target.
"""

    def autoDetectFiles(self):
        return [
            'GNUmakefile',
            'makefile',
            'Makefile',
        ]

    def _installTool(self, env):
        self._requirePackages(['make'])
        self._requireEmerge(['sys-devel/make'])
        self._requirePacman(['make'])
        self._requireApk(['make'])

    def onPrepare(self, config):
        self._callExternal([config['env']['makeBin'], 'clean'])

    def onBuild(self, config):
        target = self._getTune(config, 'build')

        if target:
            args = [target]
        else:
            args = []

        self._callExternal([config['env']['makeBin']] + args)
