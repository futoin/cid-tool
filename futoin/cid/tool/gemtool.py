
import os

from ..buildtool import BuildTool

class gemTool( BuildTool ):
    def getDeps( self ) :
        return [ 'ruby' ]
        
    def uninstallTool( self, env ):
        pass
    
    def initEnv( self, env ) :
        if env['rubyVer'] == self.SYSTEM_VER:
            gemDir = os.path.join(os.environ['HOME'], '.gem')
            gemDir = env.setdefault('gemDir', gemDir)
            os.environ['GEM_HOME'] = gemDir
            
            self._addEnvPath( 'GEM_PATH', gemDir)
            self._addBinPath( os.path.join(gemDir, 'bin'))

        super(gemTool, self).initEnv( env )
