
from citool.subtool import SubTool
import os

class nvmTool( SubTool ):
    "Node Version Manager"
    NVM_DIR_DEFAULT = os.path.join(os.environ['HOME'], '~/.nvm')

    def getType( self ):
        return self.TYPE_RUNENV

    def _installTool( self, env ):
        nvm_dir = env.get('nvmDir', self.NVM_DIR_DEFAULT)
        self._callExternal(
            [ 'bash', '-c',
              'git clone https://github.com/creationix/nvm.git {0} && \
               cd {0} && git checkout $(git describe --abbrev=0 --tags)'.format(nvm_dir) ] )
            
    def _initEnv( self, env ) :
        nvm_dir = env.get('nvmDir', self.NVM_DIR_DEFAULT)
        env['nvmDir'] = nvm_dir
        self._have_tool = os.path.exists(os.path.join(nvm_dir, 'nvm.sh'))
        
        
