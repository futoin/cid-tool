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

from ...mixins.ondemand import ext as _ext
from .. import log as _log


def mavenCentral(env):
    return env.get('mavenCentral',
                   'http://repo.maven.apache.org/maven2')


def ensureJDBC(env, lib_dir, drivers):
    ospath = _ext.ospath
    pathutil = _ext.pathutil
    ver = env.get('javaVer', '8')

    maven_central = mavenCentral(env)

    psql_ver = '42.1.3'

    if int(ver) == 7:
        psql_ver += '.jdk7'
    elif int(ver) == 6:
        psql_ver += '.jdk6'

    driverMap = {
        'mysql': ('mysql', 'mysql-connector-java', '5.1.43'),
        'postgresql': ('org/postgresql', 'postgresql', psql_ver),
        'mssql': ('com/microsoft/sqlserver', 'mssql-jdbc', '6.2.1.jre' + ver),
        'sqlite': ('org/xerial', 'sqlite-jdbc', '3.19.3'),
    }

    drivers = drivers or driverMap.keys()

    for d in drivers:
        try:
            src = driverMap[d]
        except KeyError:
            _log.errorExit('Unknown JDBC driver "{0}'.format(d))

        dst = ospath.join(lib_dir, '{0}.jar'.format(d))

        if ospath.exists(dst):
            continue

        if type(src) == tuple:
            src = '{0}/{1}/{2}/{3}/{2}-{3}.jar'.format(
                maven_central,
                src[0], src[1], src[2]
            )

        pathutil.downloadFile(env, src, dst)
