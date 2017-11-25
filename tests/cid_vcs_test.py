#
# Copyright 2015-2017 Andrey Galkin <andrey@futoin.org>
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
from futoin.cid.util import executil

import os
import subprocess
import glob

class cid_VCS_UTBase ( cid_UTBase ) :
    __test__ = False
    VCS_REPO = None
    
    @classmethod
    def setUpClass( cls ):
        super(cid_VCS_UTBase, cls).setUpClass()
        
        os.mkdir(cls.TEST_DIR)
        
    def _create_repo(self):
        raise NotImplementedError()

    def _ignore(self, path):
        raise NotImplementedError()

    def test_00_prepare( self ):
        self._create_repo()
        
        self._call_cid( [ 'vcs', 'checkout', '--vcsRepo', self.VCS_REPO, '--wcDir', 'repo_tmp' ] )
        os.chdir('repo_tmp')
        
        self._call_cid( [ 'vcs', 'branch', 'branch_A' ] )
        self._writeFile('README.txt', 'Some test')
        self._call_cid( [ 'vcs', 'commit', 'Initial commit' ] )
        
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
        rms_dir = os.path.realpath( 'rms_repo' )
        
        for p in ['Builds', 'Verified', 'Prod']:
            self._call_cid( [ 'rms', 'pool', 'create', p, '--rmsRepo', 'scp:' + rms_dir ] )

        self._call_cid( [ 'ci_build', 'branch_A', 'Builds',
                            '--vcsRepo', self.VCS_REPO,
                            '--rmsRepo', 'scp:' + rms_dir ] )
        
        self._goToBase()
        os.chdir( 'ci_build_branch_A' )

        try:
            subprocess.check_output('sha512sum -c .package.checksums',
                                    shell=True, stderr=self._stderr_log)
        except:
            if os.path.exists('/usr/bin/sha512sum'):
                raise
        
        package = sorted(os.listdir(os.path.join(rms_dir, 'Builds')))[0]
            
        package_base = os.path.basename( package )
        pkg_hash = RmsTool('name').rmsCalcHash( package_base, 'sha512' )
        os.unlink( package_base )
        self._call_cid( [ 'promote', 'Builds:Verified', package + '@' + pkg_hash,
                            '--rmsRepo', 'scp:' + rms_dir ] )
        
        self._goToBase()
        os.chdir( 'ci_build_branch_A' )
        self._call_cid( [ 'promote', 'Verified:Prod', package + '@' + pkg_hash,
                            '--rmsRepo', 'scp:' + rms_dir ] )
        
        self._goToBase()
        content = subprocess.check_output( 'tar tJf rms_repo/Prod/wc-CI-1.3.1-*.txz | /usr/bin/sort -f', shell=True )
        content = executil.toString(content)

        req_content=[
            '',
            '.package.checksums',
            'BRANCH_A',            
            'README.txt',
            'futoin.json',
            'test.json',
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
        self._call_cid( [ 'deploy', 'rms', 'Prod',
                            '--rmsRepo', 'scp:' + rms_dir ] )

        self.assertTrue(glob.glob('wc-CI-1.3.1-*'))
        
    def test_51_rms_redeploy( self ):
        rms_dir = os.path.realpath( 'rms_repo' )
        
        os.chdir( 'test_deploy' )
        self._call_cid( [ 'deploy', 'rms', 'Prod',
                            '--rmsRepo', 'scp:' + rms_dir,
                            '--redeploy'] )
        
        self.assertTrue(glob.glob('wc-CI-1.3.1-*'))
        
    def test_52_rms_deploy_package( self ):
        rms_dir = os.path.realpath( 'rms_repo' )
        
        os.chdir( 'test_deploy' )
        
        package = 'wc-1.2.4-*'

        self._call_cid( [ 'deploy', 'rms', 'Builds', package,
                            '--rmsRepo', 'scp:' + rms_dir ] )
        
        self.assertTrue(glob.glob('wc-1.2.4-*'))
        
        self._call_cid( [ 'deploy', 'rms', 'Builds', package,
                            '--rmsRepo', 'scp:' + rms_dir ] )
        
        self.assertTrue(glob.glob('wc-1.2.4-*'))
        
        self._call_cid( [ 'deploy', 'rms', 'Builds', package,
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
        
    def test_80_vcsops( self ):
        self._call_cid( [ 'vcs', 'checkout', 'branch_A', '--vcsRepo', self.VCS_REPO, '--wcDir', 'vcsops' ] )
        
        # Create new branch
        os.chdir('vcsops')
        self._call_cid( [ 'vcs', 'branch', 'branch_B' ] )
        
        self._writeFile('README.txt', 'Some other text')
        self._writeFile('test2.txt', 'New text')

        self._call_cid( [ 'vcs', 'commit', 'Some commit msg', 'README.txt', 'test2.txt' ] )

        # Verify new branch created (fresh clone)
        self._goToBase()
        self._call_cid( [ 'vcs', 'checkout', 'branch_B', '--vcsRepo', self.VCS_REPO, '--wcDir', 'vcsops2' ] )
        os.chdir('vcsops2')
        
        self.assertEqual(self._readFile('test2.txt').strip(), 'New text')
        
        # Create another branch
        self._call_cid( [ 'vcs', 'branch', 'branch_C' ] )
        
        # Delete intermediate branch
        self._goToBase()
        self._call_cid( [ 'vcs', 'delete', 'branch_B', '--vcsRepo', self.VCS_REPO ] )
        
        # Make sure branch is removed
        self._call_cid( [ 'vcs', 'checkout', 'branch_B', '--vcsRepo', self.VCS_REPO, '--wcDir', 'vcsops3' ], returncode=1 )
    
        # Export branch C
        self._call_cid( [ 'vcs', 'export', 'branch_C', 'vcsexport', '--vcsRepo', self.VCS_REPO ] )
        self.assertEqual(glob.glob('vcsexport/.*'), [])
        self.assertEqual(self._readFile('vcsexport/test2.txt').strip(), 'New text')
        
        # Re-use original wc
        self._call_cid( [ 'vcs', 'checkout', 'branch_A', '--wcDir', 'vcsops' ] )
        
        # Merge branch C
        os.chdir('vcsops')
        self._call_cid( [ 'vcs', 'merge', 'branch_C' ] )
        
        # Check merge is correct
        self._call_cid( [ 'vcs', 'checkout', 'branch_A', '--vcsRepo', self.VCS_REPO, '--wcDir', 'vcsmerged' ] )
        os.chdir('vcsmerged')
        self.assertEqual(self._readFile('test2.txt').strip(), 'New text')
        
        # Delete from WC
        self._goToBase()
        self._call_cid( [ 'vcs', 'checkout', 'branch_C', '--vcsRepo', self.VCS_REPO, '--wcDir', 'vcsdelete' ] )
        os.chdir('vcsdelete')
        self._call_cid( [ 'vcs', 'delete', 'branch_C' ] )
        
    def test_81_vcstags( self ):
        self._call_cid( [ 'vcs', 'checkout', 'branch_A', '--vcsRepo', self.VCS_REPO, '--wcDir', 'vcstags' ] )
        os.chdir('vcstags')
        
        self._call_cid( [ 'tag', 'branch_A', 'patch' ] )
        res = self._call_cid( [ 'vcs', 'tags' ], retout=True )
        res = res.strip().split("\n")
        self.assertEqual(res, [
            'v1.2.3',
            'v1.2.4',
            'v1.2.5',
            'v1.3.0',
            'v1.3.1',
            'v1.3.2',
        ])
        
        self._call_cid( [ 'tag', 'branch_A', 'minor' ] )
        res = self._call_cid( [ 'vcs', 'tags' ], retout=True )
        res = res.strip().split("\n")
        self.assertEqual(res, [
            'v1.2.3',
            'v1.2.4',
            'v1.2.5',
            'v1.3.0',
            'v1.3.1',
            'v1.3.2',
            'v1.4.0',
        ])
        
        res = self._call_cid( [ 'vcs', 'tags', 'v1.3*' ], retout=True )
        res = res.strip().split("\n")
        self.assertEqual(res, [
            'v1.3.0',
            'v1.3.1',
            'v1.3.2',
        ])
        

        self._call_cid( [ 'tag', 'branch_A', 'major' ] )
        res = self._call_cid( [ 'vcs', 'tags' ], retout=True )
        res = res.strip().split("\n")
        self.assertEqual(res, [
            'v1.2.3',
            'v1.2.4',
            'v1.2.5',
            'v1.3.0',
            'v1.3.1',
            'v1.3.2',
            'v1.4.0',
            'v2.0.0',
        ])
        
    def test_82_vcsbranches( self ):
        self._call_cid( [ 'vcs', 'checkout', 'branch_A', '--vcsRepo', self.VCS_REPO, '--wcDir', 'vcsbrch' ] )
        os.chdir('vcsbrch')
        
        self._call_cid( [ 'vcs', 'branch', 'branch_B1' ] )
        res = self._call_cid( [ 'vcs', 'branches' ], retout=True )

        res = res.strip().split("\n")
        self.assertEqual(res, [
            'branch_A',
            'branch_B1',
        ])
        
        self._call_cid( [ 'vcs', 'branch', 'branch_B2' ] )
        res = self._call_cid( [ 'vcs', 'branches' ], retout=True )
        res = res.strip().split("\n")
        self.assertEqual(res, [
            'branch_A',
            'branch_B1',
            'branch_B2'
        ])
        
        res = self._call_cid( [ 'vcs', 'branches', '*_B*' ], retout=True )
        res = res.strip().split("\n")
        self.assertEqual(res, [
            'branch_B1',
            'branch_B2'
        ])
        

        self._call_cid( [ 'vcs', 'delete', 'branch_B2' ] )
        res = self._call_cid( [ 'vcs', 'branches' ], retout=True )
        res = res.strip().split("\n")
        self.assertEqual(res, [
            'branch_A',
            'branch_B1',
        ])
        
    def test_83_vcsconflict( self ):
        self._call_cid( [ 'vcs', 'checkout', 'branch_A', '--vcsRepo', self.VCS_REPO, '--wcDir', 'vcscflct' ] )
        os.chdir('vcscflct')
        
        # Create new branches
        self._call_cid( [ 'vcs', 'branch', 'branch_C1' ] )
        self._call_cid( [ 'vcs', 'branch', 'branch_C2' ] )
        
        # Make conflicts
        self._call_cid( [ 'vcs', 'checkout', 'branch_C1' ] )
        self._writeFile('README.txt', 'Conflict 1')
        self._call_cid( [ 'vcs', 'commit', 'Msg' ] )
        
        self._call_cid( [ 'vcs', 'checkout', 'branch_C2' ] )
        self._writeFile('README.txt', 'Conflict 2')
        self._call_cid( [ 'vcs', 'commit', 'Msg' ] )
        
        # Try to merge
        self._call_cid( [ 'vcs', 'checkout', 'branch_A' ] )
        orig_list = sorted(os.listdir('.'))
        self._call_cid( [ 'vcs', 'merge', 'branch_C1' ] )
        self._call_cid( [ 'vcs', 'merge', 'branch_C2', '--no-cleanup' ], returncode=1 )
        assert ((self._readFile('README.txt').strip() != 'Conflict 1') or
                (sorted(os.listdir('.')) != orig_list))
        
        self._call_cid( [ 'vcs', 'reset' ] )
        self.assertEqual(self._readFile('README.txt').strip(), 'Conflict 1')
        self.assertEqual(sorted(os.listdir('.')), orig_list)
        
        self._call_cid( [ 'vcs', 'merge', 'branch_C2' ], returncode=1 )
        self.assertEqual(self._readFile('README.txt').strip(), 'Conflict 1')
        self.assertEqual(sorted(os.listdir('.')), orig_list)
        
        # Check working copy is clean
        self._writeFile('README.txt', 'Conflict 3')
        self._call_cid( [ 'vcs', 'commit', 'Msg 2', 'README.txt' ] )
        
        # Finalize
        self._call_cid( [ 'tag', 'branch_A', 'major' ] )
        
    def test_83_vcsmisc( self ):
        self._call_cid( [ 'vcs', 'checkout', 'branch_A', '--vcsRepo', self.VCS_REPO, '--wcDir', 'vcsmisc' ] )
        os.chdir('vcsmisc')
        
        # Create new branches
        self._call_cid( [ 'vcs', 'branch', 'branch_Dup' ] )
        self._call_cid( [ 'vcs', 'branch', 'branch_Dup' ], returncode=1 )
    
    def test_84_vcs_ismerged( self ):
        # Prepare
        self._call_cid( [ 'vcs', 'checkout', 'branch_A', '--vcsRepo', self.VCS_REPO, '--wcDir', 'vcs_ismerged' ] )
        os.chdir('vcs_ismerged')
        
        self._call_cid( [ 'vcs', 'branch', 'branch_M1' ] )
        self._writeFile('Merge1', 'Merge1')
        self._call_cid( [ 'vcs', 'commit', 'M1' ] )
        
        self._call_cid( [ 'vcs', 'checkout', 'branch_A' ] )
        self._call_cid( [ 'vcs', 'branch', 'branch_M2' ] )
        self._writeFile('Merge2', 'Merge2')
        self._call_cid( [ 'vcs', 'commit', 'M2' ] )
        
        # Not merged
        self._call_cid( [ 'vcs', 'checkout', 'branch_A' ] )
        self._call_cid( [ 'vcs', 'ismerged', 'branch_M1' ], returncode=1 )
        self._call_cid( [ 'vcs', 'ismerged', 'branch_M2' ], returncode=1 )
    
        # Merge one
        self._call_cid( [ 'vcs', 'merge', 'branch_M1' ] )
        self._call_cid( [ 'vcs', 'ismerged', 'branch_M1' ] )
        self._call_cid( [ 'vcs', 'ismerged', 'branch_M2' ], returncode=1 )
    
        # Modify merged
        self._call_cid( [ 'vcs', 'checkout', 'branch_M1' ] )
        self._writeFile('Merge1', 'Merge1-2')
        self._call_cid( [ 'vcs', 'commit', 'M1-2' ] )
        
        self._call_cid( [ 'vcs', 'checkout', 'branch_A' ] )
        self._call_cid( [ 'vcs', 'ismerged', 'branch_M1' ], returncode=1 )
        self._call_cid( [ 'vcs', 'ismerged', 'branch_M2' ], returncode=1 )

    def test_90_vcs_clean( self ):
        # Prepare
        self._call_cid( [ 'vcs', 'checkout', 'branch_A', '--vcsRepo', self.VCS_REPO, '--wcDir', 'vcs_clean' ] )
        os.chdir('vcs_clean')
        
        os.mkdir('dir2remove')
        self._writeFile(os.path.join('dir2remove', 'inner.txt'), 'INNER')
        self._writeFile('2remove.txt', 'TOP')
        self._writeFile('ignored.txt', 'IGNORED')
        self._ignore('ignored.txt')
        
        self._call_cid(['vcs', 'clean'])
        
        self.assertFalse(os.path.exists('dir2remove'))
        self.assertFalse(os.path.exists('2remove.txt'))
        self.assertFalse(os.path.exists('ignored.txt'))


#=============================================================================        
class cid_git_Test ( cid_VCS_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_VCS_UTBase.TEST_RUN_DIR, 'vcs_git')
    REPO_DIR = os.path.join( TEST_DIR, 'repo' )
    VCS_REPO = 'git:file://' + REPO_DIR
    
    def _create_repo( self ):
        self._call_cid( [ 'tool', 'exec', 'git', '--', 'init', '--bare', self.REPO_DIR ] )
        self._call_cid( [ 'tool', 'exec', 'git', '--',
                         '--git-dir',  self.REPO_DIR,
                         'symbolic-ref', 'HEAD', 'refs/heads/branch_A' ] )
        
    def _ignore(self, path):
        self._writeFile('.gitignore', path)
        
#=============================================================================
class cid_hg_Test ( cid_VCS_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_VCS_UTBase.TEST_RUN_DIR, 'vcs_hg')
    REPO_DIR = os.path.join( TEST_DIR, 'repo' )
    VCS_REPO = 'hg:' + REPO_DIR

    def _create_repo( self ):
        self._call_cid( [ 'tool', 'exec', 'hg', '--', 'init', self.REPO_DIR ] )

    def _ignore(self, path):
        self._writeFile('.hgignore', path)

#=============================================================================
class cid_svn_Test ( cid_VCS_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_VCS_UTBase.TEST_RUN_DIR, 'vcs_svn')
    REPO_DIR = os.path.join( TEST_DIR, 'repo' )
    VCS_REPO = 'svn:file://' + REPO_DIR

    def _create_repo( self ):
        self._call_cid( [ 'tool', 'install', 'svn' ] )
        subprocess.check_output(['svnadmin', 'create', self.REPO_DIR ])
        
        self._call_cid( [ 'tool', 'exec', 'svn', '--', 'mkdir', '-m', 'Creating trunk', 'file://' + self.REPO_DIR + '/trunk' ] )

    def _ignore(self, path):
        self._call_cid( [ 'tool', 'exec', 'svn', '--', 'propset', 'svn:ignore', path, '.' ] )
        
        
