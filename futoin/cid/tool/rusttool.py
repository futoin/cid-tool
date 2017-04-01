
import os

from ..runenvtool import RunEnvTool

class rustTool( RunEnvTool ):
    """Rust is a systems programming language.
    
Home: https://www.rust-lang.org
"""
    def getDeps( self ) :
        return [ 'rustup' ]

    def _installTool( self, env ):
        self._callExternal( [
            env['rustupBin'], 'toolchain', 'install', env['rustVer']
        ])
            
    def updateTool( self, env ):
        self._installTool( env )
        
    def uninstallTool( self, env ):
        self._callExternal( [
            env['rustupBin'], 'toolchain', 'uninstall', env['rustVer']
        ])
        self._have_tool = False

    def envNames( self ) :
        return ['rustBin', 'rustVer']
    
    def initEnv( self, env ) :
        ver = env.setdefault('rustVer', 'stable')
        os.environ['RUSTUP_TOOLCHAIN'] = ver
        
        try:
            res = self._callExternal( [
                env['rustupBin'], 'which', 'rustc'
            ], verbose=False)
        except:
            return

        super(rustTool, self).initEnv( env, 'rustc' )
