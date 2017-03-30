
import os, subprocess

from ..runenvtool import RunEnvTool
from .bashtoolmixin import BashToolMixIn

class gvmTool( BashToolMixIn, RunEnvTool ):
    """Go Version Manager.

Home: https://github.com/moovweb/gvm
"""
    GVM_DIR_DEFAULT = os.path.join(os.environ['HOME'], '.gvm')
    GVM_VERSION_DEFAULT = 'master'
    GVM_INSTALLER_DEFAULT = 'https://raw.githubusercontent.com/moovweb/gvm/master/binscripts/gvm-installer'

    def getDeps( self ) :
        return [ 'bash', 'git', 'hg', 'curl', 'make' ]

    def _installTool( self, env ):
        self._requireDeb(['binutils', 'bison', 'gcc', 'build-essential'])
        self._requireRpm(['bison', 'gcc', 'glibc-devel'])
        self._requireEmergeDepsOnly(['dev-lang/go'])
        self._requirePacman(['bison', 'gcc', 'glibc',])

        self._callBash( env,
              '{0} < <({1} -s -S -L {2})'
               .format(env['bashBin'], env['curlBin'], env['gvmInstaller']),
               suppress_fail=True # error when Go is not yet installed
        )
            
    def updateTool( self, env ):
        self._installTool( env )
    
    def uninstallTool( self, env ):
        gvm_dir = env['gvmDir']
        
        if os.path.exists(gvm_dir):
            self._rmTree(gvm_dir)
            
        self._have_tool = False
            
    def envNames( self ) :
        return ['gvmDir', 'gvmInstaller']
    
    def initEnv( self, env ) :
        gvm_dir = env.setdefault('gvmDir', self.GVM_DIR_DEFAULT)
        os.environ['GVM_DEST'] = os.path.dirname(gvm_dir)
        os.environ['GVM_NAME'] = os.path.basename(gvm_dir)
        os.environ['GVM_NO_UPDATE_PROFILE'] = '1'
        
        env.setdefault('gvmVer', self.GVM_VERSION_DEFAULT)
        env.setdefault('gvmInstaller', self.GVM_INSTALLER_DEFAULT)
        
        env_init = os.path.join(gvm_dir, 'scripts', 'gvm')
        env['gvmInit'] = env_init
        
        self._have_tool = os.path.exists(env_init)
        
    def onExec( self, env, args ):
        self._callBashInteractive(env,
                '. {0} && gvm {1}'
                .format(env['gvmInit'], subprocess.list2cmdline(args))
        )
