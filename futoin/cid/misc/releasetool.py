
from ..buildtool import BuildTool


class releaseTool(BuildTool):
    "FutoIn CID-specific release processing"
    __slots__ = ()

    CHANGELOG_FILE = 'CHANGELOG.txt'

    def autoDetect(self, config):
        return True

    def updateProjectConfig(self, config, updates):
        re = self._ext.re

        def py_updater(content):
            if 'version' in updates:
                return re.sub(
                    r'^.*__version__.*$',
                    '__version__ = \'{0}\''.format(updates['version']),
                    content,
                    flags=re.MULTILINE
                )

        def cl_updater(content):
            if 'version' in updates:
                date = self._ext.datetime.datetime.utcnow().isoformat().split('T')[
                    0]
                return re.sub(
                    r'^=== \(next\) ===$',
                    '=== {0} ({1}) ==='.format(updates['version'], date),
                    content,
                    count=1,
                    flags=re.MULTILINE
                )

        RELEASE_FILE = self._ospath.join('futoin', 'cid', '__init__.py')

        res = self._pathutil.updateTextFile(
            RELEASE_FILE,
            py_updater
        )
        res += self._pathutil.updateTextFile(
            self.CHANGELOG_FILE,
            cl_updater
        )
        return res

    def initEnv(self, env):
        self._have_tool = True
