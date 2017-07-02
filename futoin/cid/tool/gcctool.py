
from ..runenvtool import RunEnvTool


class gccTool(RunEnvTool):
    """GNU Compiler Collection.

Home: https://gcc.gnu.org/

If gccBin is set it must point to bin folder.
"""
    __slots__ = ()

    def envNames(self):
        return ['gccBin', 'gccPrefix', 'gccPostfix']

    def _installTool(self, env):
        self._install.deb(['gcc'])
        self._install.rpm(['gcc'])
        self._install.emerge(['sys-devel/gcc'])
        self._install.pacman(['gcc'])
        self._install.apk(['gcc'])

    def initEnv(self, env):
        gcc_bin = env.get('gccBin', None)

        pref = env.setdefault('gccPrefix', '')
        postf = env.setdefault('gccPostfix', '')

        if gcc_bin:
            if self._ospath.exists(gcc_bin):
                self._have_tool = True
        else:
            gcc = pref + 'gcc' + postf
            gcc = self._pathutil.which(gcc)

            if gcc:
                env['gccBin'] = gcc
                self._have_tool = True
