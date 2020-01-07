#
# Copyright 2015-2020 Andrey Galkin <andrey@futoin.org>
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

from __future__ import print_function, absolute_import

from .cid_utbase import cid_UTBase
from futoin.cid.rmstool import RmsTool
from futoin.cid.util import executil as _executil
from futoin.cid.util import pathutil as _pathutil
from futoin.cid.util import install as _install

import os
import subprocess
import glob
import shutil
import pwd
import time
import json

class cid_RMSHost_UTBase ( cid_UTBase ) :
    __test__ = False
    
    @classmethod
    def setUpClass( cls ):
        super(cid_RMSHost_UTBase, cls).setUpClass()
        
        os.mkdir(cls.TEST_DIR)
        os.chdir(cls.TEST_DIR)
        cls._createRepo()
    
    @classmethod
    def _createRepo( cls ):
        pass

    def test_ok( self ):
        self.assertEqual(1, 1)
        


#=============================================================================        
class cid_archiva_Test ( cid_RMSHost_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_RMSHost_UTBase.TEST_RUN_DIR, 'rms_archiva')
    ARC_URL = 'http://localhost:8084/'
    RMS_REPO = 'archiva:' + ARC_URL

    @classmethod
    def _createRepo( cls ):
        try:
            cls._call_cid(['tool', 'exec', 'docker', '--',
                       'start', 'rms_archiva'])
        except:
            # Original from: https://github.com/KamikazeLux/apacheArchiva/blob/master/Dockerfile
            cls._writeFile('Dockerfile', '''
FROM openjdk:jre

ENV ARCHIVA_VERSION 2.2.1
ENV ARCHIVA_BASE /var/archiva

RUN curl -sSLo /tmp/apache-archiva-$ARCHIVA_VERSION-bin.tar.gz http://apache.mirrors.tds.net/archiva/$ARCHIVA_VERSION/binaries/apache-archiva-$ARCHIVA_VERSION-bin.tar.gz \
  && tar -xf /tmp/apache-archiva-$ARCHIVA_VERSION-bin.tar.gz --directory /opt \
  && rm /tmp/apache-archiva-$ARCHIVA_VERSION-bin.tar.gz

RUN adduser archiva

WORKDIR /opt/apache-archiva-$ARCHIVA_VERSION

RUN sed -i "/set.default.ARCHIVA_BASE/c\set.default.ARCHIVA_BASE=$ARCHIVA_BASE" conf/wrapper.conf
RUN mkdir -p $ARCHIVA_BASE/logs $ARCHIVA_BASE/data $ARCHIVA_BASE/temp $ARCHIVA_BASE/conf
RUN mv conf/* $ARCHIVA_BASE/conf
RUN chown -R archiva:archiva $ARCHIVA_BASE

# temp fix because ARCHIVA_BASE is not use by archiva :(
RUN rmdir logs conf temp
RUN ln -s $ARCHIVA_BASE/logs logs
RUN ln -s $ARCHIVA_BASE/conf conf
RUN ln -s $ARCHIVA_BASE/data data
RUN ln -s $ARCHIVA_BASE/temp temp

#VOLUME /var/archiva
USER archiva

EXPOSE 8080
CMD bin/archiva console
''')
            cls._call_cid(['build'])
            cls._call_cid(['tool', 'exec', 'docker', '--',
                        'run', '--name', 'rms_archiva', '-d',
                        '-p', '8084:8080',
                        '-m', '512m',
                        'rms_archiva'])


#=============================================================================        
class cid_artifactory_Test ( cid_RMSHost_UTBase ) :
    # Disabled as Pro version is required, use manual testing run "tests/cid_rms_test.py:cid_artifactory_Test"
    __test__ = True
    TEST_DIR = os.path.join(cid_RMSHost_UTBase.TEST_RUN_DIR, 'rms_artifactory')
    RT_URL = 'http://localhost:8083/artifactory'
    RMS_REPO = 'artifactory:' + RT_URL
    HASH_LIST = ('md5', 'sha1', 'sha256')

    @classmethod
    def _createRepo( cls ):
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'pull', 'docker.bintray.io/jfrog/artifactory-pro:latest'])
        try:
            cls._call_cid(['tool', 'exec', 'docker', '--',
                        'run', '--name', 'rms_artifactory', '-d',
                        '-p', '8083:8081',
                        '-m', '512m',
                        'docker.bintray.io/jfrog/artifactory-pro:latest'])
        except:
            cls._call_cid(['tool', 'exec', 'docker', '--',
                       'start', 'rms_artifactory'])


#=============================================================================        
class cid_nexus_Test ( cid_RMSHost_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_RMSHost_UTBase.TEST_RUN_DIR, 'rms_nexus')
    NXS_URL = 'http://localhost:8081/nexus'
    RMS_REPO = 'nexus:' + NXS_URL
    HASH_LIST = ('md5', 'sha1')

    @classmethod
    def _createRepo( cls ):
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'pull', 'sonatype/nexus:oss'])
        try:
            cls._call_cid(['tool', 'exec', 'docker', '--',
                        'run', '--name', 'rms_nexus', '-d',
                        '-p', '8081:8081',
                        '-m', '512m',
                        'sonatype/nexus:oss'])
        except:
            cls._call_cid(['tool', 'exec', 'docker', '--',
                       'start', 'rms_nexus'])
    
#=============================================================================        
class cid_nexus3_Test ( cid_RMSHost_UTBase ) :
    # Nexus 3.x does have REST API, only provisioning scripts
    # Not fully supported.
    __test__ = False
    TEST_DIR = os.path.join(cid_RMSHost_UTBase.TEST_RUN_DIR, 'rms_nexus3')
    NXS_URL = 'http://localhost:8082'
    RMS_REPO = 'nexus3:' + NXS_URL

    @classmethod
    def _createRepo( cls ):
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'pull', 'sonatype/nexus3'])
        try:
            cls._call_cid(['tool', 'exec', 'docker', '--',
                        'run', '--name', 'rms_nexus3', '-d',
                        '-p', '8082:8081',
                        '-m', '512m',
                        'sonatype/nexus3'])
        except:
            cls._call_cid(['tool', 'exec', 'docker', '--',
                       'start', 'rms_nexus3'])

#=============================================================================        
class cid_mysql_Test ( cid_UTBase ) :
    __test__ = True
    _create_test_dir = True
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'db_mysql')
    
    def test_setup(self):
        _install.debrpm(['mysql-server', 'mysql-client'])
        mysql = _pathutil.which('mysql')
        _executil.callExternal([mysql, '-uroot', '-h', '127.0.0.1', '-e',
                            "GRANT ALL PRIVILEGES ON *.* TO 'cid'@'%' IDENTIFIED BY 'cid'"],
                            verbose=False)
        _executil.callExternal([mysql, '-uroot', '-h', '127.0.0.1', '-e',
                            "DROP DATABASE IF EXISTS flyway;"
                            "CREATE DATABASE flyway CHARACTER SET utf8; "
                            "GRANT ALL PRIVILEGES ON flyway.* TO 'flyway'@'%' IDENTIFIED BY 'flyway'"],
                            verbose=False)
        _executil.callExternal([mysql, '-uroot', '-h', '127.0.0.1', '-e',
                            "DROP DATABASE IF EXISTS liquibase;"
                            "CREATE DATABASE liquibase CHARACTER SET utf8; "
                            "GRANT ALL PRIVILEGES ON liquibase.* TO 'liquibase'@'%' IDENTIFIED BY 'liquibase'"],
                            verbose=False)
        _executil.callExternal([mysql, '-uroot', '-h', '127.0.0.1', '-e',
                            "DROP DATABASE IF EXISTS redmine;"
                            "CREATE DATABASE redmine CHARACTER SET utf8; "
                            "GRANT ALL PRIVILEGES ON redmine.* TO 'redmine'@'%' IDENTIFIED BY 'redmine'"],
                            verbose=False)
        _executil.callExternal([mysql, '-uroot', '-h', '127.0.0.1', '-e',
                            "DROP DATABASE IF EXISTS redmine_trunk;"
                            "CREATE DATABASE redmine_trunk CHARACTER SET utf8; "
                            "GRANT ALL PRIVILEGES ON redmine_trunk.* TO 'redmine'@'%' IDENTIFIED BY 'redmine'"],
                            verbose=False)
        _executil.callExternal([mysql, '-uroot', '-h', '127.0.0.1', '-e',
                            "DROP DATABASE IF EXISTS nextcloud;"
                            "CREATE DATABASE nextcloud CHARACTER SET utf8; "
                            "GRANT ALL PRIVILEGES ON nextcloud.* TO 'nextcloud'@'%' IDENTIFIED BY 'nextcloud'"],
                            verbose=False)
