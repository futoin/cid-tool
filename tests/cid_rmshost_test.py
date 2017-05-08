
from __future__ import print_function, absolute_import

from .cid_utbase import cid_UTBase
from futoin.cid.rmstool import RmsTool

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
