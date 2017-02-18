
from citool.subtool import SubTool
import os

class nvmTool( SubTool ):
    "Node Version Manager"
    NVM_DIR_DEFAULT = os.path.join(os.environ['HOME'], '.nvm')

    def getType( self ):
        return self.TYPE_RUNENV

    def getDeps( self ) :
        return [ 'bash' ]

    def _installTool( self, env ):
        nvm_dir = env['nvmDir']
        nvm_git = env.setdefault('nvmGit', 'https://github.com/creationix/nvm.git')
        bash_bin = env['bashBin']

        self._callExternal(
            [ bash_bin, '-c',
              'git clone {1} {0} && \
               cd {0} && git checkout $(git describe --abbrev=0 --tags)'
               .format(nvm_dir, nvm_git) ] )
            
    def _initEnv( self, env ) :
        nvm_dir = env.setdefault('nvmDir', self.NVM_DIR_DEFAULT)
        self._have_tool = os.path.exists(os.path.join(nvm_dir, 'nvm.sh'))
        
        
