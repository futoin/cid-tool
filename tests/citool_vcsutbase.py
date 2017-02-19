
from .citool_utbase import citool_UTBase
from citool.subtool import SubTool

import os
import subprocess

class citool_VCSUTBase ( citool_UTBase ) :
    @classmethod
    def setUpClass( cls ):
        super(citool_VCSUTBase, cls).setUpClass()
        
        test_tar = os.path.basename( cls.TEST_DIR )
        cmd = [
            '/bin/tar', 'xf',
            os.path.join(os.path.dirname(__file__), test_tar + '.tar'),
            '-C', cls.TEST_RUN_DIR
        ]
        subprocess.check_output( cmd, stdin=subprocess.PIPE )
    
    def test_10_tag( self ):
        self._call_citool( [ 'tag', 'branch_A', '--vcsRepo', self.VCS_REPO ] )
        
    def test_20_tag_ver( self ):
        self._call_citool( [
            'tag', 'branch_A', '1.3.0',
            '--vcsRepo', self.VCS_REPO,
            '--wcDir', 'build_ver' ] )
        
    def test_30_prepare( self ):
        self._call_citool( [ 'prepare', 'branch_A', '--vcsRepo', self.VCS_REPO, '--wcDir', 'prep_dir' ] )
        self._goToBase()
        self._call_citool( [ 'prepare', 'v1.2.3', '--wcDir', 'prep_dir' ] )
        self._goToBase()
        os.chdir( 'prep_dir' )
        self._call_citool( [ 'prepare', 'branch_A' ] )
    
    def test_40_ci_build_deploy( self ):
        try:
            os.makedirs( 'rms_repo/Builds')
            os.makedirs( 'rms_repo/Verified')
            os.makedirs( 'rms_repo/Prod')
        except :
            pass
        
        rms_dir = os.path.realpath( 'rms_repo' )

        self._call_citool( [ 'ci_build', 'branch_A', 'Builds',
                            '--vcsRepo', self.VCS_REPO,
                            '--rmsRepo', 'scp:' + rms_dir ] )
        
        self._goToBase()
        os.chdir( 'build' )
        package = subprocess.check_output( 'cd %s && ls Builds/*.txz | head -1' % rms_dir, shell=True )
        try:
            package = str(package, 'utf8').strip()
        except TypeError:
            package = str(package).strip()
            
        package_base = os.path.basename( package )
        pkg_hash = SubTool.rmsCalcHash( package_base, 'sha512' )
        os.unlink( package_base )
        self._call_citool( [ 'promote', package, 'Verified',
                            '--rmsRepo', 'scp:' + rms_dir,
                            '--rmsHash', pkg_hash ] )
        
        self._goToBase()
        os.chdir( 'build' )
        self._call_citool( [ 'promote', package, 'Prod',
                            '--rmsRepo', 'scp:' + rms_dir,
                            '--rmsHash', pkg_hash ] )
        
        self._goToBase()
        content = subprocess.check_output( 'tar tJf rms_repo/Prod/wc-CI-1.3.0-*.txz | /usr/bin/sort -f', shell=True )
        try:
            content = str(content, 'utf8')
        except TypeError:
            content = str(content)
        req_content=[
            '',
            './',
            './bower.json',
            './bower.json.gz',
            './BRANCH_A',
            './composer.json',
            './composer.json.gz',
            './Gruntfile.js',
            './Gruntfile.js.gz',
            './node_modules/',
            './.package.checksums',
            './package.json',
            './package.json.gz',
            './vendor/',
            './vendor/autoload.php',
            './vendor/composer/',
            './vendor/composer/autoload_classmap.php',
            './vendor/composer/autoload_namespaces.php',
            './vendor/composer/autoload_psr4.php',
            './vendor/composer/autoload_real.php',
            './vendor/composer/autoload_static.php',
            './vendor/composer/ClassLoader.php',
            './vendor/composer/LICENSE',
            './vendor/composer/installed.json',
            './vendor/composer/installed.json.gz',
        ]
        self.maxDiff = 1024
        content = sorted(content.split("\n"))
        req_content = sorted(req_content)
        self.assertEqual( content, req_content )
        
        #------------
        self._goToBase()
        os.makedirs( 'test_deploy' )
        os.chdir( 'test_deploy' )
        self._call_citool( [ 'deploy', 'Prod',
                            '--rmsRepo', 'scp:' + rms_dir ] )
        