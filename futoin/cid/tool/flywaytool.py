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


class flywayTool(MigrationTool):
    """Flyway - Evolve your Database Schema easily and
reliably across all your instances.

Home: https://flywaydb.org/

Migration is run automatically, if flyway.conf is found.

FLYWAY_HOME is user/set similar to LIQUIBASE_HOME

Note: for now, it gets the latest tag from GitHub and then uses
    maven repo for download. That obviously should be improved.
"""
    __slots__ = ()

    FLYWAY_CONF = 'flyway.conf'

    def autoDetectFiles(self):
        return self.FLYWAY_CONF

    def getDeps(self):
        return ['java', 'tar', 'gzip']

    def getVersionParts(self):
        return 3

    def envNames(self):
        return ['flywayVer', 'flywayDir', 'flywayDrivers']

    def _installTool(self, env):
        ospath = self._ospath
        os = self._os
        github = self._ext.github

        lb_dir = env['flywayDir']
        ver = env.get('flywayVer', 'latest')

        if ver == 'latest':
            release = ver
        else:
            release = 'tags/flyway-{0}'.format(ver)

        info = github.releaseInfo(env, 'flyway/flyway', release)

        found_ver = info['tag_name'].replace('flyway-', '')
        dst = ospath.join(lb_dir, found_ver)

        if not ospath.exists(dst):
            maven_central = self._install.mavenCentral(env)
            asset_url = '{0}/org/flywaydb/flyway-commandline/{1}/flyway-commandline-{1}.tar.gz'.format(
                maven_central, found_ver
            )
            self._pathutil.downloadExtract(
                env, asset_url,
                dst, 'z', 1)

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
        ver = env.get('flywayVer', 'latest')
        inst_dir = env['flywayDir']

        if ver != 'latest':
            inst_dir = self._pathutil.safeJoin(inst_dir, ver)

        self._pathutil.rmTree(inst_dir)

    def initEnv(self, env):
        ospath = self._ospath

        # ---
        inst_dir = self._environ.get('FLYWAY_HOME', None)
        fail_on_missing = False

        if inst_dir:
            fail_on_missing = True
        else:
            lb_dir = ospath.join(
                self._pathutil.userHome(),
                '.local', 'flywaybin')
            lb_dir = env.setdefault('flywayDir', lb_dir)
            ver = env.get('flywayVer', 'latest')
            inst_dir = ospath.join(lb_dir, ver)

        lb_bin = ospath.join(inst_dir, 'flyway')

        if ospath.exists(lb_bin):
            env['flywayBin'] = lb_bin
            self._environ['FLYWAY_HOME'] = inst_dir
            self._have_tool = True
        elif fail_on_missing:
            self._errorExit('Unset FLYWAY_HOME or '
                            'setup the tool manually.')

    def onMigrate(self, config):
        if self._ospath.exists(self.FLYWAY_CONF):
            self.onExec(config['env'], ['-n', 'migrate'], replace=False)
