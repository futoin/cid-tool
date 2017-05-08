
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

class cid_RMS_UTBase ( cid_UTBase ) :
    __test__ = False
    RMS_HOST = '10.11.1.11'
    TEST_REPOS = ('CIBuilds', 'ReleaseBuilds', 'Verified', 'Prod')
    HASH_LIST = ('md5', 'sha1', 'sha256', 'sha512')
    
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
        
        if not os.path.exists( os.path.join(ssh_dir, 'id_rsa.pub') ):
            subprocess.check_output( [ 'ssh-keygen', '-q',
                                      '-t', 'rsa',
                                      '-b', '2048',
                                      '-N', '',
                                      '-f', os.path.join(ssh_dir, 'id_rsa') ],
                                       stderr=cls._dev_null )

        shutil.copy(os.path.join(ssh_dir, 'id_rsa.pub'), 'authorized_keys')
        
    @classmethod
    def _addSshHost( cls, port, user ):
        pwdres = pwd.getpwuid(os.geteuid())
        ssh_dir = os.path.join(pwdres[5], '.ssh')
        
        if os.path.exists(os.path.join(ssh_dir, 'known_hosts')):
            subprocess.check_output(
                    [ 'ssh-keygen', '-R', '[localhost]:{0}'.format(port) ],
                    stderr=cls._dev_null )
        
        cls._call_cid(['tool', 'exec', 'ssh', '--',
                       '-n',
                       '-o', 'BatchMode=yes',
                       '-o', 'StrictHostKeyChecking=no',
                       '-p', str(port), user+'@localhost',
                       'false',
                      ], ignore=True)
        
    def test_00_create_pool( self ):
        for r in self.TEST_REPOS:
            self._call_cid(['rms', 'pool', 'create', r, '--rmsRepo', self.RMS_REPO])
        
    def test_01_create_pool_existing( self ):
        self._call_cid(['rms', 'pool', 'create', 'Prod', '--rmsRepo', self.RMS_REPO])

    def test_02_create_pool_list( self ):
        res = self._call_cid( ['rms', 'pool', 'list', '--rmsRepo', self.RMS_REPO], retout=True )
    
        res = res.strip().split("\n")
        test = list(self.TEST_REPOS)

        if 'ignore' in res:
            test += ['ignore']

        self.assertEquals(res, sorted(test))
        
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
        
        hash_vals = {
            'md5' : '@md5:0e422e37ef47223b51391cb375294d5b',
            'sha1' : '@sha1:ce934892855dcfd27df743116abfe00fb70360cd',
            'sha256' : '@sha256:f8c5cbac4201b75babbf8ddc6abbcd1618e5a3f8bc6c1afa2a2344269701e07e',
            'sha512' : '@sha512:fa12de9d7e1bb827ee78779ea4586da2465a43e51f1089ca40e01d3495905cee4aefe33589fcf3407235d5a9dda1f0d3fd1b2eb7ab65b2495fa7113ffa7b486a',
        }
        
        if 'sha256' not in self.HASH_LIST:
            hash = hash_vals[self.HASH_LIST[0]]
        else :
            hash = hash_vals['sha256']
                
        invhash = hash.split(':')
        invhash[1] = invhash[1][::-1]
        invhash = ':'.join(invhash)
        
        self._call_cid(['promote', 'CIBuilds', package_file, '--rmsRepo', self.RMS_REPO]) 
        self._call_cid(['promote', 'CIBuilds:Prod', package + invhash, '--rmsRepo', self.RMS_REPO], returncode=1) 
        self._call_cid(['promote', 'CIBuilds:Verified', package + hash, '--rmsRepo', self.RMS_REPO]) 
        self._call_cid(['rms', 'retrieve', 'Prod', package + invhash, '--rmsRepo', self.RMS_REPO], returncode=1) 
    
        for ht in self.HASH_LIST:
            self._call_cid(['rms', 'retrieve', 'Verified', package + hash, '--rmsRepo', self.RMS_REPO])
            os.remove(package)
            
    def test_30_rms_subpath( self ):
        self._writeFile(os.path.join('packages', 'package-subpath-2.1.3.txt'), 'Package subpath 2.1.3')
        self._writeFile(os.path.join('packages', 'package-subpath-2.3.txt'), 'Package subpath 2.3')
        self._call_cid(['promote', 'CIBuilds/sub/path'] + glob.glob(os.path.join('packages', 'package-subpath*')) + ['--rmsRepo', self.RMS_REPO]) 
        self._call_cid(['promote', 'CIBuilds/sub/path'] + glob.glob(os.path.join('packages', 'package-subpath*')) + ['--rmsRepo', self.RMS_REPO], returncode=1) 
        self._call_cid(['promote', 'CIBuilds/sub/path:ReleaseBuilds/sub/path', 'package-subpath-2.1.3.txt', 'package-subpath-2.3.txt', '--rmsRepo', self.RMS_REPO])
        self._call_cid(['promote', 'CIBuilds/sub/path:ReleaseBuilds/sub/path', 'package-subpath-2.1.3.txt', 'package-subpath-2.3.txt', '--rmsRepo', self.RMS_REPO], returncode=1)
        
        res = self._call_cid(['rms', 'list', 'ReleaseBuilds/sub/path', '--rmsRepo', self.RMS_REPO], retout=True).strip()
        res = res.split("\n")
        self.assertEqual(res, ['package-subpath-2.1.3.txt', 'package-subpath-2.3.txt'])
        
        self._call_cid(['rms', 'retrieve', 'ReleaseBuilds/sub/path', 'package-subpath-2.1.3.txt', '--rmsRepo', self.RMS_REPO])
        assert os.path.exists('package-subpath-2.1.3.txt')

        


#=============================================================================        
class cid_archiva_Test ( cid_RMS_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_RMS_UTBase.TEST_RUN_DIR, 'rms_archiva')
    ARC_URL = 'http://{0}:8084/'.format(cid_RMS_UTBase.RMS_HOST)
    RMS_REPO = 'archiva:' + ARC_URL

    @classmethod
    def _createRepo( cls ):
        cls._writeJSON(os.path.join(os.environ['HOME'], '.futoin.json'), {
            'env': {
                'archivaUser' : 'admin',
                'archivaPassword' : 'Password1',
            }
        })
            
        for i in range(1, 180):
            if cls._call_cid(['tool', 'exec', 'curl', '--',
                        '-fsSL',
                        '-X', 'GET',
                        '{0}restServices/archivaServices/pingService/ping'.format(cls.ARC_URL)
                        ], ignore=True) :
                break
            else:
                time.sleep(1)
                
        # create admin user
        if cls._call_cid(['tool', 'exec', 'curl', '--',
                        '-fsSL',
                        '-X', 'GET',
                        '{0}restServices/redbackServices/userService/isAdminUserExists'.format(cls.ARC_URL)
                        ], ignore=True, retout=True) != 'true' :
            cls._call_cid(['tool', 'exec', 'curl', '--',
                    '-fsSL',
                    '-H', 'Content-Type: application/json',
                    '-X', 'POST',
                    '{0}restServices/redbackServices/userService/createAdminUser'.format(cls.ARC_URL),
                    '-d', json.dumps({
                        "assignedRoles": [],
                        "email" : "admin@example.com",
                        "fullName" : "Admin",
                        "locked" : False,
                        "password" : "Password1",
                        "confirmPassword" : "Password1",
                        "passwordChangeRequired" : False,
                        "permanent" : True,
                        "readOnly" : False,
                        "username" : "admin",
                        "validated" : True,
                    })
                ])
                
        #
        repos = cls._call_cid(['rms', 'pool', 'list', '--rmsRepo={0}'.format(cls.RMS_REPO)], retout=True)
        repos = repos.strip().split("\n")
        repos = list(filter(None, repos))

        for r in repos:
            cls._call_cid(['tool', 'exec', 'curl', '--',
                        '-fsSL', '-u', 'admin:Password1',
                        '-X', 'GET',
                        '{0}restServices/archivaServices/managedRepositoriesService/deleteManagedRepository?deleteContent=true&repositoryId={1}'.format(cls.ARC_URL, r)
                        ])

#=============================================================================        
class cid_artifactory_Test ( cid_RMS_UTBase ) :
    # Disabled as Pro version is required, use manual testing run "tests/cid_rms_test.py:cid_artifactory_Test"
    __test__ = False
    TEST_DIR = os.path.join(cid_RMS_UTBase.TEST_RUN_DIR, 'rms_artifactory')
    RT_URL = 'http://{0}:8083/artifactory'.format(cid_RMS_UTBase.RMS_HOST)
    RMS_REPO = 'artifactory:' + RT_URL
    HASH_LIST = ('md5', 'sha1', 'sha256')

    @classmethod
    def _createRepo( cls ):
        # Workaround JFrog CLI #52 - https://github.com/JFrogDev/jfrog-cli-go/issues/52
        try: os.remove(os.path.join(os.environ['HOME'], '.jfrog', 'jfrog-cli.conf'))
        except: pass
    
        cls._writeJSON(os.path.join(os.environ['HOME'], '.futoin.json'), {
            'env': {
                'artifactoryUser' : 'admin',
                'artifactoryPassword' : 'password',
            }
        })
            
        for i in range(1, 180):
            if cls._call_cid(['rms', 'pool', 'list', '--rmsRepo={0}'.format(cls.RMS_REPO)], ignore=True):
                break
            else:
                time.sleep(1)
                
        #
        cls._call_cid(['rms', 'pool', 'create', 'ignore', '--rmsRepo={0}'.format(cls.RMS_REPO)], ignore=True)
        repos = cls._call_cid(['rms', 'pool', 'list', '--rmsRepo={0}'.format(cls.RMS_REPO)], retout=True)
        repos = repos.strip().split("\n")
        try:
            del repos[repos.index('ignore')]
        except ValueError:
            pass

        for r in repos:
            cls._call_cid(['tool', 'exec', 'curl', '--',
                        '-fsSL', '-u', 'admin:password',
                        '-X', 'DELETE',
                        '{0}/{1}'.format(cls.RT_URL, r)
                        ])


#=============================================================================        
class cid_nexus_Test ( cid_RMS_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_RMS_UTBase.TEST_RUN_DIR, 'rms_nexus')
    NXS_URL = 'http://{0}:8081/nexus'.format(cid_RMS_UTBase.RMS_HOST)
    RMS_REPO = 'nexus:' + NXS_URL
    HASH_LIST = ('md5', 'sha1')

    @classmethod
    def _createRepo( cls ):
        cls._writeJSON(os.path.join(os.environ['HOME'], '.futoin.json'), {
            'env': {
                'nexusUser' : 'admin',
                'nexusPassword' : 'admin123',
            }
        })
            
        for i in range(1, 180):
            if cls._call_cid(['rms', 'pool', 'list', '--rmsRepo={0}'.format(cls.RMS_REPO)], ignore=True):
                break
            else:
                time.sleep(1)
                
        # Repos may depend on other repos - ignore error on first run
        for ignore in (True, False):
            repos = cls._call_cid(['rms', 'pool', 'list', '--rmsRepo={0}'.format(cls.RMS_REPO)], retout=True)
            repos = repos.strip()
            
            if not repos:
                 break
            
            repos = repos.split("\n")
            
            for r in repos:
                cls._call_cid(['tool', 'exec', 'curl', '--',
                            '-fsSL', '-u', 'admin:admin123',
                            '-X', 'DELETE',
                            '{0}/service/local/repositories/{1}'.format(cls.NXS_URL, r)
                            ], ignore=ignore)
    
#=============================================================================        
class cid_nexus3_Test ( cid_RMS_UTBase ) :
    # Nexus 3.x does have REST API, only provisioning scripts
    # Not fully supported.
    __test__ = False
    TEST_DIR = os.path.join(cid_RMS_UTBase.TEST_RUN_DIR, 'rms_nexus3')
    NXS_URL = 'http://{0}:8082'.format(cid_RMS_UTBase.RMS_HOST)
    RMS_REPO = 'nexus3:' + NXS_URL

    @classmethod
    def _createRepo( cls ):
        cls._writeJSON(os.path.join(os.environ['HOME'], '.futoin.json'), {
            'env': {
                'nexus3User' : 'admin',
                'nexus3Password' : 'admin123',
            }
        })
            
        for i in range(1, 180):
            if cls._call_cid(['rms', 'pool', 'list', '--rmsRepo={0}'.format(cls.RMS_REPO)], ignore=True):
                break
            else:
                time.sleep(1)
                
        # Repos may depend on other repos - ignore error on first run
        for ignore in (True, False):
            repos = cls._call_cid(['rms', 'pool', 'list', '--rmsRepo={0}'.format(cls.RMS_REPO)], retout=True)
            repos = repos.strip()
            
            if not repos:
                 break
            
            repos = repos.split("\n")
            
            for r in repos:
                cls._call_cid(['tool', 'exec', 'curl', '--',
                        '-fsSL', '-u', 'admin:admin123',
                        '-X', 'DELETE',
                        '{0}/repositories/{1}'.format(cls.NXS_URL, r)
                        ], ignore=True)

#=============================================================================        
class cid_scp_Test ( cid_RMS_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_RMS_UTBase.TEST_RUN_DIR, 'rms_scp')
    RMS_REPO = 'scp:ssh://rms@localhost/8022:rmsroot'

    @classmethod
    def _createRepo( cls ):
        cls._genSSH()
        cls._writeFile('Dockerfile', '''
FROM debian:stable-slim
RUN useradd -m -d /rms -U rms && mkdir /rms/.ssh
COPY authorized_keys /rms/.ssh/
RUN apt-get update && apt-get install -y openssh-server && \
    chmod 700 /rms/.ssh/ && chmod 600 /rms/.ssh/* && \
    mkdir /var/run/sshd  && \
    chown -R rms:rms /rms
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
''')
        cls._removeRepo(True)
        
        cls._call_cid(['build'])
        
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'run', '--name', 'rmstest', '-d',
                       '-m', '512m',
                       '-p', '8022:22',
                       'rms_scp'])
        
        cls._addSshHost(8022, 'scp')
    
    @classmethod
    def _removeRepo( cls, ignore=False ):
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'stop', 'rmstest'], ignore=ignore)
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'rm', 'rmstest'], ignore=ignore)


#=============================================================================        
class cid_svn_Test ( cid_RMS_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_RMS_UTBase.TEST_RUN_DIR, 'rms_svn')
    RMS_REPO = 'svn:svn+ssh://rms@localhost:8022/rms'

    @classmethod
    def _createRepo( cls ):
        cls._genSSH()
        cls._writeFile('Dockerfile', '''
FROM debian:stable-slim
RUN useradd -m -d /rms -U rms && mkdir /rms/.ssh
COPY authorized_keys /rms/.ssh/
RUN apt-get update && apt-get install -y openssh-server && \
    chmod 700 /rms/.ssh/ && chmod 600 /rms/.ssh/* && \
    mkdir /var/run/sshd  && \
    chown -R rms:rms /rms
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]

RUN apt-get install -y subversion
RUN svnadmin create /rms/rmsroot && chown -R rms:rms /rms/rmsroot
RUN sed -i -e 's@ssh-rsa@command="/usr/bin/svnserve -r /rms/rmsroot -t --tunnel-user=svnuser",no-pty ssh-rsa@' /rms/.ssh/authorized_keys
''')
        cls._removeRepo(True)
        
        cls._call_cid(['build'])
        
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'run', '--name', 'rmstest', '-d',
                       '-m', '512m',
                       '-p', '8022:22',
                       'rms_svn'])
        cls._addSshHost(8022, 'svn')
    
    @classmethod
    def _removeRepo( cls, ignore=False ):
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'stop', 'rmstest'], ignore=ignore)
        cls._call_cid(['tool', 'exec', 'docker', '--',
                       'rm', 'rmstest'], ignore=ignore)

