
import os

from ..runenvtool import RunEnvTool

class phpbuildTool( RunEnvTool ):
    "php build tool"
    PHPBUILD_DIR_DEFAULT = os.path.join(os.environ['HOME'], '.phpbuild')
    PHPBUILD_LATEST = 'master'

    def getDeps( self ) :
        return [ 'bash', 'git' ]

    def _installTool( self, env ):
        phpbuild_dir = env['phpbuildDir']
        phpbuild_git = env.get('phpbuildGit', 'https://github.com/php-build/php-build.git')
        phpbuild_ver = env.get('phpbuildVer', self.PHPBUILD_LATEST) 
        bash_bin = env['bashBin']
        
        self._callExternal(
            [ bash_bin,  '--noprofile', '--norc', '-c',
              'git clone {1} {0}; \
               cd {0} && git fetch && git reset --hard && git checkout {2}'
               .format(phpbuild_dir, phpbuild_git, phpbuild_ver) ] )
            
    def updateTool( self, env ):
        phpbuild_dir = env['phpbuildDir']
        phpbuild_ver = env.get('phpbuildVer', self.PHPBUILD_LATEST) 
        bash_bin = env['bashBin']

        self._callExternal(
            [ bash_bin,  '--noprofile', '--norc', '-c',
              'cd {0} && git fetch && git reset --hard && git checkout {1} && git pull --rebase'
               .format(phpbuild_dir, phpbuild_ver) ] )
    
    def uninstallTool( self, env ):
        phpbuild_dir = env['phpbuildDir']
        bash_bin = env['bashBin']
        self._callExternal(
            [ bash_bin,  '--noprofile', '--norc', '-c',
              'chmod -R g+w {0}; rm -rf {0}'
               .format(phpbuild_dir) ] )
        self._have_tool = False
            
    def _envNames( self ) :
        return ['phpbuildDir', 'phpbuildBin', 'phpbuildGit', 'phpbuildVer']
    
    def initEnv( self, env ) :
        phpbuild_dir = env.setdefault('phpbuildDir', self.PHPBUILD_DIR_DEFAULT)
        phpbuild_bin = env.setdefault('phpbuildBin', os.path.join(phpbuild_dir, 'bin', 'php-build'))
        self._have_tool = os.path.exists(phpbuild_bin)
