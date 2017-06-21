
import os

from ..runenvtool import RunEnvTool


class binutilsTool(RunEnvTool):
    """GNU Binutils.

Home: https://www.gnu.org/software/binutils/

If binutilsDir is set it must point to bin folder.
"""

    def envNames(self):
        return ['binutilsDir', 'binutilsPrefix', 'binutilsPostfix']

    def _installTool(self, env):
        self._requireDeb(['binutils'])
        self._requireRpm(['binutils'])
        self._requireEmerge(['sys-devel/binutils'])
        self._requirePacman(['binutils'])
        self._requireApk(['binutils'])

    def initEnv(self, env):
        pref = env.setdefault('binutilsPrefix', '')
        postf = env.setdefault('binutilsPostfix', '')

        bu_dir = env.get('binutilsDir', None)
        ld = pref + 'ld' + postf

        if bu_dir:
            ld = os.path.join(bu_dir, ld)
            self._have_tool = os.path.exists(bu_dir)
        else:
            ld = self._which(ld)

            if ld:
                env['binutilsDir'] = os.path.dirname(ld)
                self._have_tool = True
