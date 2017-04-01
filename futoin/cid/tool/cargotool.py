
import os

from ..buildtool import BuildTool
from ..testtool import TestTool

class cargoTool( BuildTool, TestTool ):
    """Cargo, Rust;s Package Manager.
    
Home: http://doc.crates.io/

Build targets:
    prepare -> clean
    build -> build
    check -> test
Override targets with .config.toolTune.

"""
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'Cargo.toml' ]
        )
        
    def getDeps( self ) :
        return [ 'rust' ]
        
    def uninstallTool( self, env ):
        pass
    
    def onPrepare( self, config ):
        self._callExternal( [
            config['env']['cargoBin'], 'clean',
        ])
    
    def onBuild( self, config ):
        args = []
        
        if not config.get('debugBuild', False):
            args.append('--release')
        
        
        self._callExternal( [ config['env']['cargoBin'], 'build' ] + args)
    
    def onPackage( self, config ):
        pass

    def onCheck( self, config ):
        self._callExternal( [ config['env']['cargoBin'], 'test' ])
        
    def onRunDev( self, config ):
        self._callExternal( [ config['env']['cargoBin'], 'run' ])


        

