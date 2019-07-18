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

from ..migrationtool import MigrationTool


class liquibaseTool(MigrationTool):
    """Liquibase - source control for your database.

Home: http://www.liquibase.org/

If LIQUIBASE_HOME is set, the tool must be installed manually.
If liquibaseVer is used, it must be set to full version (GitHub API limitation).

Liquibase migrate is run only if liquibase.properties file is present.
"changeLogFile" must be set in liquibase.properties.

Required drivers can be controlled through liquibaseDrivers variable.
Currently supported:
* mysql
* postgresql
* sqlite
* mssql

Others, are more JVM-specific and most likely will be bundled with JVM app.
"""
    __slots__ = ()

    LIQUIBASE_PROPERTIES = 'liquibase.properties'

    def autoDetectFiles(self):
        return self.LIQUIBASE_PROPERTIES

    def getDeps(self):
        return ['java', 'tar', 'gzip']

    def getVersionParts(self):
        return 3

    def envNames(self):
        return ['liquibaseVer', 'liquibaseDir', 'liquibaseDrivers']

    def _installTool(self, env):
        ospath = self._ospath
        os = self._os
        github = self._ext.github

        lb_dir = env['liquibaseDir']
        ver = env.get('liquibaseVer', 'latest')

        if ver == 'latest':
            release = ver
        else:
            release = 'tags/liquibase-parent-{0}'.format(ver)

        info = github.releaseInfo(env, 'liquibase/liquibase', release)

        found_ver = info['name'].replace('v', '')
        dst = ospath.join(lb_dir, found_ver)
        asset = github.findAsset(info['assets'], 'application/x-gzip')

        if not ospath.exists(dst):
            self._pathutil.downloadExtract(
                env, asset['browser_download_url'],
                dst, 'z')

        if ver == 'latest':
            latest = ospath.join(lb_dir, 'latest')
            try:
                os.unlink(latest)
            except OSError:
                pass
            os.symlink(found_ver, latest)

    def _updateTool(self, env):
        self._installTool(env)

    def uninstallTool(self, env):
        ver = env.get('liquibaseVer', 'latest')
        inst_dir = env['liquibaseDir']

        if ver != 'latest':
            inst_dir = self._pathutil.safeJoin(inst_dir, ver)

        self._pathutil.rmTree(inst_dir)

    def initEnv(self, env):
        ospath = self._ospath

        # ---
        inst_dir = self._environ.get('LIQUIBASE_HOME', None)
        fail_on_missing = False

        if inst_dir:
            fail_on_missing = True
        else:
            lb_dir = ospath.join(
                self._pathutil.userHome(),
                '.local', 'liquibasebin')
            lb_dir = env.setdefault('liquibaseDir', lb_dir)
            ver = env.get('liquibaseVer', 'latest')
            inst_dir = ospath.join(lb_dir, ver)

        lb_bin = ospath.join(inst_dir, 'liquibase')

        if ospath.exists(lb_bin):
            self._install.ensureJDBC(
                env,
                ospath.join(inst_dir, 'lib'),
                env.get('liquibaseDrivers', '').split())
            env['liquibaseBin'] = lb_bin
            self._environ['LIQUIBASE_HOME'] = inst_dir
            self._have_tool = True
        elif fail_on_missing:
            self._errorExit('Unset LIQUIBASE_HOME or '
                            'setup the tool manually.')

    def onMigrate(self, config):
        if self._ospath.exists(self.LIQUIBASE_PROPERTIES):
            self.onExec(config['env'], ['update'], replace=False)
