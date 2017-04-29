
from __future__ import print_function, absolute_import

from .cid_utbase import cid_UTBase
from futoin.cid.rmstool import RmsTool

import os
import subprocess
import glob
import shutil
import pwd

class cid_RMS_UTBase ( cid_UTBase ) :
    __test__ = False
    
    @classmethod
    def setUpClass( cls ):
        super(cid_RMS_UTBase, cls).setUpClass()
        
        os.mkdir(cls.TEST_DIR)
        os.chdir(cls.TEST_DIR)
        cls._createRepo()

    @classmethod
    def tearDownClass( cls ):
        cls._removeRepo()
    
    @classmethod
    def _createRepo( cls ):
        pass

    @classmethod
    def _removeRepo( cls ):
        pass

    @classmethod
    def _genSSH( cls ):
        pwdres = pwd.getpwuid(os.geteuid())
        ssh_dir = os.path.join(pwdres[5], '.ssh')
        
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir)
        else:
            subprocess.check_output( [ 'ssh-keygen', '-R', 'localhost' ] )
        
        if not os.path.exists( os.path.join(ssh_dir, 'id_rsa.pub') ):
            subprocess.check_output( [ 'ssh-keygen', '-q',
                                      '-t', 'rsa',
                                      '-b', '2048',
                                      '-N', '',
                                      '-f', os.path.join(ssh_dir, 'id_rsa') ] )

        shutil.copy(os.path.join(ssh_dir, 'id_rsa.pub'), 'authorized_keys')
        
        
    def test_00_create_pool( self ):
        self._call_cid(['rms', 'pool', 'create', 'CIBuilds', '--rmsRepo', self.RMS_REPO])
        self._call_cid(['rms', 'pool', 'create', 'ReleaseBuilds', '--rmsRepo', self.RMS_REPO])
        self._call_cid(['rms', 'pool', 'create', 'Verified', '--rmsRepo', self.RMS_REPO])
        self._call_cid(['rms', 'pool', 'create', 'Prod', '--rmsRepo', self.RMS_REPO])
        
    def test_01_create_pool_existing( self ):
        self._call_cid(['rms', 'pool', 'create', 'Prod', '--rmsRepo', self.RMS_REPO])

    def test_02_create_pool_list( self ):
        res = self._call_cid( ['rms', 'pool', 'list', '--rmsRepo', self.RMS_REPO], retout=True )
    
        res = res.strip().split("\n")

        self.assertEquals(res, ['CIBuilds', 'Prod', 'ReleaseBuilds', 'Verified'])
        
    def test_10_rms_upload( self ):
        os.makedirs('packages')
        self._writeFile(os.path.join('packages', 'package-CI-1.2.3.txt'), 'Package 1.2.3')
        self._writeFile(os.path.join('packages', 'package-CI-1.3.txt'), 'Package 1.3')
        
        self._call_cid(['promote', 'CIBuilds'] + glob.glob(os.path.join('packages', 'package-CI*')) + ['--rmsRepo', self.RMS_REPO]) 
        self._call_cid(['promote', 'CIBuilds'] + glob.glob(os.path.join('packages', 'package-CI*')) + ['--rmsRepo', self.RMS_REPO], returncode=1) 
        
    def test_11_rms_promote( self ):
        self._call_cid(['promote', 'CIBuilds:ReleaseBuilds', 'package-CI-1.2.3.txt', 'package-CI-1.3.txt', '--rmsRepo', self.RMS_REPO])
        self._call_cid(['promote', 'CIBuilds:ReleaseBuilds', 'package-CI-1.2.3.txt', 'package-CI-1.3.txt', '--rmsRepo', self.RMS_REPO], returncode=1)
        self._call_cid(['promote', 'ReleaseBuilds:Verified', 'package-CI-1.2.3.txt', '--rmsRepo', self.RMS_REPO])
        self._call_cid(['promote', 'ReleaseBuilds:Verified', 'package-CI-1.2.3.txt', '--rmsRepo', self.RMS_REPO], returncode=1)
        self._call_cid(['promote', 'ReleaseBuilds:Prod', 'package-CI-1.3.txt', '--rmsRepo', self.RMS_REPO])
        self._call_cid(['promote', 'ReleaseBuilds:Prod', 'package-CI-1.3.txt', '--rmsRepo', self.RMS_REPO], returncode=1)
        
    def test_12_rms_list( self ):
        res = self._call_cid(['rms', 'list', 'Prod', '--rmsRepo', self.RMS_REPO], retout=True).strip()
        self.assertEqual(res, 'package-CI-1.3.txt')

        res = self._call_cid(['rms', 'list', 'Verified', '--rmsRepo', self.RMS_REPO], retout=True).strip()
        self.assertEqual(res, 'package-CI-1.2.3.txt')
        
    def test_13_rms_retrieve( self ):
        self._call_cid(['rms', 'retrieve', 'Prod', 'package-CI-1.3.txt', '--rmsRepo', self.RMS_REPO])
        assert os.path.exists('package-CI-1.3.txt')
        
    def test_20_rms_hashtest( self ):
        package = 'package-hash.txt'
        package_file = os.path.join('packages', package)
        self._writeFile(package_file, 'Package Hash')
        
        hash = '@sha256:f8c5cbac4201b75babbf8ddc6abbcd1618e5a3f8bc6c1afa2a2344269701e07e'
        invhash = '@sha256:c5f9a4f423aa38961bd5d7f0815d56587bd08067621e02c5706244c75ea0fc9f'
        
        self._call_cid(['promote', 'CIBuilds', package_file, '--rmsRepo', self.RMS_REPO]) 
        self._call_cid(['promote', 'CIBuilds:Prod', package + invhash, '--rmsRepo', self.RMS_REPO], returncode=1) 
        self._call_cid(['promote', 'CIBuilds:Verified', package + hash, '--rmsRepo', self.RMS_REPO]) 
        self._call_cid(['rms', 'retrieve', 'Prod', package + invhash, '--rmsRepo', self.RMS_REPO], returncode=1) 
        self._call_cid(['rms', 'retrieve', 'Verified', package + hash, '--rmsRepo', self.RMS_REPO]) 
        
        


#=============================================================================        
class cid_archiva_Test ( cid_RMS_UTBase ) :
    #__test__ = True
    TEST_DIR = os.path.join(cid_RMS_UTBase.TEST_RUN_DIR, 'rms_archiva')
    RMS_REPO = 'archiva:http://localhost:80'

    @classmethod
    def _createRepo( cls ):
        pass
    
    @classmethod
    def _removeRepo( cls ):
        pass

#=============================================================================        
class cid_artifactory_Test ( cid_RMS_UTBase ) :
    #__test__ = True
    TEST_DIR = os.path.join(cid_RMS_UTBase.TEST_RUN_DIR, 'rms_artifactory')
    RMS_REPO = 'artifactory:http://localhost:8081'

    @classmethod
    def _createRepo( cls ):
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'pull', 'docker.bintray.io/jfrog/artifactory-oss:latest'])
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'run', '--name', 'artifactory', '-d',
                       '-p', '8081:8081',
                       'docker.bintray.io/jfrog/artifactory-oss:latest'])
    
    @classmethod
    def _removeRepo( cls ):
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'stop', 'artifactory'])
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'rm', 'artifactory'])

#=============================================================================        
class cid_nexus_Test ( cid_RMS_UTBase ) :
    #__test__ = True
    TEST_DIR = os.path.join(cid_RMS_UTBase.TEST_RUN_DIR, 'rms_nexus')
    RMS_REPO = 'nexus:http://localhost:80'

    @classmethod
    def _createRepo( cls ):
        pass
    
    @classmethod
    def _removeRepo( cls ):
        pass

#=============================================================================        
class cid_scp_Test ( cid_RMS_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_RMS_UTBase.TEST_RUN_DIR, 'rms_scp')
    RMS_REPO = 'scp:ssh://scp@localhost/8022:rmsroot'

    @classmethod
    def _createRepo( cls ):
        cls._genSSH()
        cls._writeFile('Dockerfile', '''
FROM debian:stable-slim
RUN apt-get update && apt-get install -y openssh-server
RUN useradd -m -d /scp -U scp && mkdir /scp/.ssh
COPY authorized_keys /scp/.ssh/
RUN chmod 700 /scp/.ssh/ && chmod 600 /scp/.ssh/*
RUN mkdir /scp/rmsroot/
RUN mkdir /var/run/sshd
RUN chown -R scp:scp /scp
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
''')
        cls._removeRepoA(True)
        
        cls._call_cid(['build'])
        
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'run', '--name', 'scp', '-d',
                       '-p', '8022:22', 'rms_scp'])
    
    @classmethod
    def _removeRepoA( cls, ignore=False ):
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'stop', 'scp'], ignore=ignore)
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'rm', 'scp'], ignore=ignore)
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'rmi', 'rms_scp'], ignore=ignore)


#=============================================================================        
class cid_svn_Test ( cid_RMS_UTBase ) :
    #__test__ = True
    TEST_DIR = os.path.join(cid_RMS_UTBase.TEST_RUN_DIR, 'rms_svn')
    RMS_REPO = 'svn:http://localhost:80'

    @classmethod
    def _createRepo( cls ):
        pass
    
    @classmethod
    def _removeRepo( cls ):
        pass

