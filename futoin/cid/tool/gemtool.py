
import os

from ..buildtool import BuildTool

class gemTool( BuildTool ):
    def getDeps( self ) :
        return [ 'ruby' ]
        
    def uninstallTool( self, env ):
        pass
    
    def initEnv( self, env ) :
        installArgs = []
        
        if env['rubyVer'] == self.SYSTEM_VER:
            gemDir = os.path.join(os.environ['HOME'], '.gem')
            gemDir = env.setdefault('gemDir', gemDir)
            os.environ['GEM_HOME'] = gemDir
            
            self._addEnvPath( 'GEM_PATH', gemDir)
            self._addBinPath( os.path.join(gemDir, 'bin'))
            installArgs += ['--no-user-install', '--no-format-executable']

        super(gemTool, self).initEnv( env )

        if self._have_tool:
            version = self._callExternal([env['gemBin'], '--version'], verbose=False).strip()
            
            if version >= '2':
                installArgs += ['--no-document']
            else :
                installArgs += ['--no-ri', '--no-rdoc']
                
            env['gemInstallArgs'] = installArgs
