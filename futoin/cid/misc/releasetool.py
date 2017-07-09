
from ..buildtool import BuildTool


class releaseTool(BuildTool):
    """FutoIn CID-specific release processing

Python: replaces "*__version__"' with "__version__ = '{version}'"
Changelog: replaces "=== \(next\) ===" with "=== {version} ({date}) ==="

Tune:
    .python = [] - list of Python files
    .changelog = 'CHANGELOG.txt' - list of ChangeLog files
"""
    __slots__ = ()

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

        res = []
        #---
        py_files = self._getTune(config, 'python', [])
        py_files = self._configutil.listify(py_files)

        for pyf in py_files:
            res += self._pathutil.updateTextFile(pyf, py_updater)

        #---
        cl_files = self._getTune(config, 'changelog', 'CHANGELOG.txt')
        cl_files = self._configutil.listify(cl_files)

        for clf in cl_files:
            res += self._pathutil.updateTextFile(clf, cl_updater)

        #---
        return res

    def initEnv(self, env):
        self._have_tool = True
