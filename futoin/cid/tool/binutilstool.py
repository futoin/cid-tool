
from ..runenvtool import RunEnvTool


class binutilsTool(RunEnvTool):
    """GNU Binutils.

Home: https://www.gnu.org/software/binutils/

If binutilsDir is set it must point to bin folder.
"""
    __slots__ = ()

    def envNames(self):
        return ['binutilsDir', 'binutilsPrefix', 'binutilsPostfix']

    def _installTool(self, env):
        self._install.deb(['binutils'])
        self._install.rpm(['binutils'])
        self._install.emerge(['sys-devel/binutils'])
        self._install.pacman(['binutils'])
        self._install.apk(['binutils'])

    def initEnv(self, env):
        ospath = self._ospath
        pref = env.setdefault('binutilsPrefix', '')
        postf = env.setdefault('binutilsPostfix', '')

        bu_dir = env.get('binutilsDir', None)
        ld = pref + 'ld' + postf

        if bu_dir:
            ld = ospath.join(bu_dir, ld)
            self._have_tool = ospath.exists(bu_dir)
        else:
            ld = self._pathutil.which(ld)

            if ld:
                env['binutilsDir'] = ospath.dirname(ld)
                self._have_tool = True
