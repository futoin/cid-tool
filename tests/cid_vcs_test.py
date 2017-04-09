
from __future__ import print_function, absolute_import

from .cid_utbase import cid_UTBase
from futoin.cid.rmstool import RmsTool

import os
import subprocess
import glob

class cid_VCS_UTBase ( cid_UTBase ) :
    __test__ = False
    
    @classmethod
    def setUpClass( cls ):
        super(cid_VCS_UTBase, cls).setUpClass()
        
        os.mkdir(cls.TEST_DIR)
    
    def test_00_prepare( self ):
        self._create_repo()
        self._goToBase()
        
        self._call_cid( [
                'prepare', 'branch_A',
                '--vcsRepo', self.VCS_REPO,
                '--wcDir', 'repo_prep' ] )
        os.chdir('repo_prep')
        
        self._writeFile('BRANCH_A', 'aaaa')
        self._writeJSON('test.json', {})
        self._writeJSON('futoin.json', {
            'name' : 'wc',
            'version' : '0.0.1',
        })
        
        self._call_cid( [ 'vcs', 'commit', 'Added FutoIn support'] )
        self._call_cid( [ 'tag', 'branch_A', '1.2.3'] )
        self._call_cid( [ 'tag', 'branch_A', '1.2.4'] )

    def test_10_tag( self ):
        self._call_cid( [
                'tag', 'branch_A',
                '--vcsRepo', self.VCS_REPO,
                '--wcDir', 'build_ver' ] )
        
    def test_20_tag_invalid_ver( self ):
        self._call_cid( [
            'tag', 'branch_A', 'v1.2.6',
            '--vcsRepo', self.VCS_REPO,
            '--wcDir', 'build_ver' ], returncode=1 )
        
    def test_21_tag_ver( self ):
        self._call_cid( [
            'tag', 'branch_A', '1.3.0',
            '--vcsRepo', self.VCS_REPO,
            '--wcDir', 'build_ver' ] )

    def test_22_tag_ver( self ):
        self._call_cid( [
            'tag', 'branch_A',
            '--wcDir', 'build_ver' ] )
            
    def test_30_prepare( self ):
        self._call_cid( [ 'prepare', 'branch_A', '--vcsRepo', self.VCS_REPO, '--wcDir', 'prep_dir' ] )
        self._goToBase()
        self._call_cid( [ 'prepare', 'v1.2.3', '--wcDir', 'prep_dir' ] )
        self._goToBase()
        os.chdir( 'prep_dir' )
        self._call_cid( [ 'prepare', 'branch_A' ] )
    
    def test_40_ci_build( self ):
        try:
            os.makedirs( 'rms_repo/Builds')
            os.makedirs( 'rms_repo/Verified')
            os.makedirs( 'rms_repo/Prod')
        except :
            pass
        
        rms_dir = os.path.realpath( 'rms_repo' )

        self._call_cid( [ 'ci_build', 'branch_A', 'Builds',
                            '--vcsRepo', self.VCS_REPO,
                            '--rmsRepo', 'scp:' + rms_dir ] )
        
        self._goToBase()
        os.chdir( 'ci_build' )
        package = subprocess.check_output( 'cd %s && ls Builds/*.txz | head -1' % rms_dir, shell=True )
        try:
            package = str(package, 'utf8').strip()
        except TypeError:
            package = str(package).strip()
            
        package_base = os.path.basename( package )
        pkg_hash = RmsTool.rmsCalcHash( package_base, 'sha512' )
        os.unlink( package_base )
        self._call_cid( [ 'promote', package, 'Verified',
                            '--rmsRepo', 'scp:' + rms_dir,
                            '--rmsHash', pkg_hash ] )
        
        self._goToBase()
        os.chdir( 'ci_build' )
        self._call_cid( [ 'promote', package, 'Prod',
                            '--rmsRepo', 'scp:' + rms_dir,
                            '--rmsHash', pkg_hash ] )
        
        self._goToBase()
        content = subprocess.check_output( 'tar tJf rms_repo/Prod/wc-CI-1.3.1-*.txz | /usr/bin/sort -f', shell=True )
        try:
            content = str(content, 'utf8')
        except TypeError:
            content = str(content)
        req_content=[
            '',
            './',
            './.package.checksums',
            './BRANCH_A',            
            './README.txt',
            './README.txt.gz',
            './futoin.json',
            './futoin.json.gz',
            './test.json',
            './test.json.gz',
        ]
        self.maxDiff = 1024
        content = sorted(content.split("\n"))
        req_content = sorted(req_content)
        self.assertEqual( content, req_content )
        
    def test_40_release_build( self ):
        rms_dir = os.path.realpath( 'rms_repo' )

        # no release
        self._call_cid( [ 'ci_build', 'v1.2.4',
                            '--vcsRepo', self.VCS_REPO ] )
        
        self.assertFalse(glob.glob(os.path.join(rms_dir, 'Builds', 'wc-1.2.4-*')))

        self._call_cid( [ 'ci_build', 'v1.2.4', 'Builds',
                            '--vcsRepo', self.VCS_REPO,
                            '--rmsRepo', 'scp:' + rms_dir ] )
        
        self.assertTrue(glob.glob(os.path.join(rms_dir, 'Builds', 'wc-1.2.4-*')))
        
    def test_50_rms_deploy( self ):
        rms_dir = os.path.realpath( 'rms_repo' )
        
        os.makedirs( 'test_deploy' )
        os.chdir( 'test_deploy' )
        self._call_cid( [ 'deploy', 'Prod',
                            '--rmsRepo', 'scp:' + rms_dir ] )

        self.assertTrue(glob.glob('wc-CI-1.3.1-*'))
        
    def test_51_rms_redeploy( self ):
        rms_dir = os.path.realpath( 'rms_repo' )
        
        os.chdir( 'test_deploy' )
        self._call_cid( [ 'deploy', 'Prod',
                            '--rmsRepo', 'scp:' + rms_dir,
                            '--redeploy'] )
        
        self.assertTrue(glob.glob('wc-CI-1.3.1-*'))
        
    def test_52_rms_deploy_package( self ):
        rms_dir = os.path.realpath( 'rms_repo' )
        
        os.chdir( 'test_deploy' )
        
        package = 'wc-1.2.4-*'

        self._call_cid( [ 'deploy', 'Builds', package,
                            '--rmsRepo', 'scp:' + rms_dir ] )
        
        self.assertTrue(glob.glob('wc-1.2.4-*'))
        
        self._call_cid( [ 'deploy', 'Builds', package,
                            '--rmsRepo', 'scp:' + rms_dir ] )
        
        self.assertTrue(glob.glob('wc-1.2.4-*'))
        
        self._call_cid( [ 'deploy', 'Builds', package,
                            '--rmsRepo', 'scp:' + rms_dir,
                            '--redeploy' ] )
        
        self.assertTrue(glob.glob('wc-1.2.4-*'))

    def test_60_vcstag_deploy( self ):
        os.chdir( 'test_deploy' )
        
        self._call_cid( [ 'deploy', 'vcstag', '--vcsRepo', self.VCS_REPO ] )
        self.assertTrue(os.path.exists('v1.3.1'))
        
        self._call_cid( [ 'deploy', 'vcstag', '--vcsRepo', self.VCS_REPO ] )
        self.assertTrue(os.path.exists('v1.3.1'))
        
        self._call_cid( [ 'deploy', 'vcstag', '--vcsRepo', self.VCS_REPO, '--redeploy' ] )
        self.assertTrue(os.path.exists('v1.3.1'))
        
    def test_61_vcstag_deploy_ref( self ):
        os.chdir( 'test_deploy' )
        
        self._call_cid( [ 'deploy', 'vcstag', '--vcsRepo', self.VCS_REPO, 'v1.2.*' ] )
        self.assertTrue(os.path.exists('v1.2.5'))

        self._call_cid( [ 'deploy', 'vcstag', '--vcsRepo', self.VCS_REPO, 'v1.2.5' ] )
        self.assertTrue(os.path.exists('v1.2.5'))

        self._call_cid( [ 'deploy', 'vcstag', '--vcsRepo', self.VCS_REPO, 'v1.2.*', '--redeploy' ] )
        self.assertTrue(os.path.exists('v1.2.5'))
        
        self._call_cid( [ 'deploy', 'vcstag', '--vcsRepo', self.VCS_REPO, 'v1.2.4' ] )
        self.assertTrue(os.path.exists('v1.2.4'))
        
    def test_70_vcsref_deploy( self ):
        os.chdir( 'test_deploy' )
        
        self._call_cid( [ 'deploy', 'vcsref', 'branch_A', '--vcsRepo', self.VCS_REPO ] )
        self.assertTrue(glob.glob('branch_A_*'))
        
        self._call_cid( [ 'deploy', 'vcsref', 'branch_A', '--vcsRepo', self.VCS_REPO ] )
        self.assertTrue(glob.glob('branch_A_*'))
        
        self._call_cid( [ 'deploy', 'vcsref', 'branch_A', '--vcsRepo', self.VCS_REPO, '--redeploy' ] )
        self.assertTrue(glob.glob('branch_A_*'))
        

#=============================================================================        
class cid_git_Test ( cid_VCS_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_VCS_UTBase.TEST_RUN_DIR, 'vcs_git')
    REPO_DIR = os.path.join( TEST_DIR, 'repo' )
    VCS_REPO = 'git:' + REPO_DIR
    
    def _create_repo( self ):
        self._call_cid( [ 'tool', 'exec', 'git', '--', 'init', '--bare', self.REPO_DIR ] )
        self._call_cid( [ 'tool', 'exec', 'git', '--', 'clone', self.REPO_DIR, 'repo_tmp' ] )
        os.chdir('repo_tmp')
        self._writeFile('README.txt', 'Some test')
        self._call_cid( [ 'tool', 'exec', 'git', '--',
                         'add', '-A' ] )
        self._call_cid( [ 'tool', 'exec', 'git', '--',
                         'config', 'user.email', 'test@example.com' ] )
        self._call_cid( [ 'tool', 'exec', 'git', '--',
                         'config', 'user.name', 'unit test' ] )
        self._call_cid( [ 'tool', 'exec', 'git', '--',
                         'commit', '-m', 'Initial commit' ] )
        self._call_cid( [ 'tool', 'exec', 'git', '--',
                         'checkout', '-b', 'branch_A' ] )
        self._call_cid( [ 'tool', 'exec', 'git', '--',
                         'push', 'origin', 'master', 'branch_A' ] )
        
        
        
#=============================================================================
class cid_hg_Test ( cid_VCS_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_VCS_UTBase.TEST_RUN_DIR, 'vcs_hg')
    REPO_DIR = os.path.join( TEST_DIR, 'repo' )
    VCS_REPO = 'hg:' + REPO_DIR

    def _create_repo( self ):
        self._call_cid( [ 'tool', 'exec', 'hg', '--', 'init', self.REPO_DIR ] )
        os.chdir(self.REPO_DIR)
        self._call_cid( [ 'tool', 'exec', 'hg', '--', 'branch', 'branch_A' ] )
        self._writeFile('README.txt', 'Some test')
        self._call_cid( [ 'tool', 'exec', 'hg', '--', 'commit', '-A', '-m', 'Initial commit' ] )

#=============================================================================
class cid_svn_Test ( cid_VCS_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_VCS_UTBase.TEST_RUN_DIR, 'vcs_svn')
    REPO_DIR = os.path.join( TEST_DIR, 'repo' )
    VCS_REPO = 'svn:file://' + REPO_DIR

    def _create_repo( self ):
        self._call_cid( [ 'tool', 'install', 'svn' ] )
        subprocess.check_output(['svnadmin', 'create', self.REPO_DIR ])
        
        url = 'file://'+self.REPO_DIR + '/branches/branch_A'
        
        os.mkdir('repo_tmp')
        self._writeFile('repo_tmp/README.txt', 'Some test')
        self._call_cid( [ 'tool', 'exec', 'svn', '--', 'import', '-m', 'Initial commit', 'repo_tmp', url ] )
        
