
import os

from ..runenvtool import RunEnvTool


class gccTool(RunEnvTool):
    """GNU Compiler Collection.

Home: https://gcc.gnu.org/

If gccBin is set it must point to bin folder.
"""

    def envNames(self):
        return ['gccBin', 'gccPrefix', 'gccPostfix']

    def _installTool(self, env):
        self._requireDeb(['gcc'])
        self._requireRpm(['gcc'])
        self._requireEmerge(['sys-devel/gcc'])
        self._requirePacman(['gcc'])
        self._requireApk(['gcc'])

    def initEnv(self, env):
        gcc_bin = env.get('gccBin', None)

        pref = env.setdefault('gccPrefix', '')
        postf = env.setdefault('gccPostfix', '')

        if gcc_bin:
            if os.path.exists(gcc_bin):
                self._have_tool = True
        else:
            gcc = pref + 'gcc' + postf
            gcc = self._which(gcc)

            if gcc:
                env['gccBin'] = gcc
                self._have_tool = True
