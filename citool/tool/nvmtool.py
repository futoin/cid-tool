
from citool.subtool import SubTool
import os

class nvmTool( SubTool ):
    "Node Version Manager"
    NVM_DIR_DEFAULT = os.path.join(os.environ['HOME'], '.nvm')
    NVM_LATEST = '$(git describe --abbrev=0 --tags --match "v[0-9]*")'

    def getType( self ):
        return self.TYPE_RUNENV

    def getDeps( self ) :
        return [ 'bash' ]

    def _installTool( self, env ):
        nvm_dir = env['nvmDir']
        nvm_git = env.get('nvmGit', 'https://github.com/creationix/nvm.git')
        nvm_ver = env.get('nvmVer', self.NVM_LATEST) 
        bash_bin = env['bashBin']

        self._callExternal(
            [ bash_bin,  '--noprofile', '--norc', '-c',
              'git clone {1} {0} && \
               cd {0} && git checkout {2}'
               .format(nvm_dir, nvm_git, nvm_ver) ] )
            
    def updateTool( self, env ):
        nvm_dir = env['nvmDir']
        nvm_ver = env.get('nvmVer', self.NVM_LATEST) 
        bash_bin = env['bashBin']

        self._callExternal(
            [ bash_bin,  '--noprofile', '--norc', '-c',
              'cd {0} && git fetch && git checkout {1}'
               .format(nvm_dir, nvm_ver) ] )
        
            
    def initEnv( self, env ) :
        nvm_dir = env.setdefault('nvmDir', self.NVM_DIR_DEFAULT)
        self._have_tool = os.path.exists(os.path.join(nvm_dir, 'nvm.sh'))
