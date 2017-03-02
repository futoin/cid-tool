
from ..subtool import SubTool
import os

class nvmTool( SubTool ):
    "Node Version Manager"
    NVM_DIR_DEFAULT = os.path.join(os.environ['HOME'], '.nvm')
    NVM_LATEST = '$(git describe --abbrev=0 --tags --match "v[0-9]*")'

    def getType( self ):
        return self.TYPE_RUNENV

    def getDeps( self ) :
        return [ 'bash', 'git', 'curl' ]

    def _installTool( self, env ):
        nvm_dir = env['nvmDir']
        nvm_git = env.get('nvmGit', 'https://github.com/creationix/nvm.git')
        nvm_ver = env.get('nvmVer', self.NVM_LATEST) 
        bash_bin = env['bashBin']

        self._callExternal(
            [ bash_bin,  '--noprofile', '--norc', '-c',
              'git clone {1} {0}; \
               cd {0} && git fetch && git reset --hard && git checkout {2}'
               .format(nvm_dir, nvm_git, nvm_ver) ] )
            
    def updateTool( self, env ):
        nvm_dir = env['nvmDir']
        nvm_ver = env.get('nvmVer', self.NVM_LATEST) 
        bash_bin = env['bashBin']

        self._callExternal(
            [ bash_bin,  '--noprofile', '--norc', '-c',
              'cd {0} && git fetch && git reset --hard && git checkout {1}'
               .format(nvm_dir, nvm_ver) ] )
    
    def uninstallTool( self, env ):
        nvm_dir = env['nvmDir']
        bash_bin = env['bashBin']
        self._callExternal(
            [ bash_bin,  '--noprofile', '--norc', '-c',
              'chmod -R g+w {0}; rm -rf {0}'
               .format(nvm_dir) ] )
        self._have_tool = False
            
    def _envNames( self ) :
        return ['nvmDir', 'nvmGit', 'nvmVer']
    
    def initEnv( self, env ) :
        nvm_dir = env.setdefault('nvmDir', self.NVM_DIR_DEFAULT)
        self._have_tool = os.path.exists(os.path.join(nvm_dir, 'nvm.sh'))
