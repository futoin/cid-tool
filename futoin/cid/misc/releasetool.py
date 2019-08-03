#
# Copyright 2015-2019 Andrey Galkin <andrey@futoin.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from ..buildtool import BuildTool


class releaseTool(BuildTool):
    """FutoIn CID-specific release processing

Go:
- replaces version parts according to .govars
Python:
- replaces "*__version__"' with "__version__ = '{version}'"
Changelog:
- replaces "=== \(next\) ===" with "=== {version} ({date}) ==="
- replaces "# \(next\)" with "# {version} ({date})"

Tune:
    .python = [] - list of Python files
    .changelog = 'CHANGELOG.txt' - list of ChangeLog files
    .go = [] - list of Go files to update
    .govars = ['VersionMajor', 'VersionMinor', 'VersionPath']
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
                version = updates['version']
                date = self._ext.datetime.datetime.utcnow().isoformat().split('T')[
                    0]
                content = re.sub(
                    r'^=== \(next\) ===$',
                    '=== {0} ({1}) ==='.format(version, date),
                    content,
                    count=1,
                    flags=re.MULTILINE
                )
                content = re.sub(
                    r'# \(next\)',
                    '# {0} ({1})'.format(version, date),
                    content,
                    count=1,
                    flags=re.MULTILINE
                )
                return content

        def go_updater(content):
            if 'version' in updates:
                ver = updates['version'].split('.')
                for i in range(len(ver)):
                    vn = go_vars[i]
                    vv = ver[i]
                    content = re.sub(
                        r'^(.*){0} = \d+(.*)$'.format(vn),
                        r'\1{0} = {1}\2'.format(vn, vv),
                        content,
                        flags=re.MULTILINE
                    )
                return content

        res = []
        # ---
        py_files = self._getTune(config, 'python', [])
        py_files = self._configutil.listify(py_files)

        for pyf in py_files:
            res += self._pathutil.updateTextFile(pyf, py_updater)

        # ---
        cl_files = self._getTune(config, 'changelog', 'CHANGELOG.txt')
        cl_files = self._configutil.listify(cl_files)

        for clf in cl_files:
            res += self._pathutil.updateTextFile(clf, cl_updater)

        # ---
        go_files = self._getTune(config, 'go', [])
        go_files = self._configutil.listify(go_files)
        go_vars = self._getTune(config, 'govars', [
            'VersionMajor',
            'VersionMinor',
            'VersionPatch',
        ])

        for gof in go_files:
            res += self._pathutil.updateTextFile(gof, go_updater)

        # ---
        return res

    def initEnv(self, env):
        self._have_tool = True
