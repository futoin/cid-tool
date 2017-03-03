
import os, shutil

from ..buildtool import BuildTool

class setuptoolsTool( BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'setup.py' ]
        )
    
    def getDeps( self ) :
        return [ 'python', 'pip', 'venv' ]
    
    def _installTool( self, env ):
        self._callExternal( [ env['pipBin'], 'install', '-q', 'setuptools' ] )
        
    def updateTool( self, env ):
        self._callExternal( [ env['pipBin'], 'install', '-q', '--upgrade', 'setuptools' ] )
        
    def uninstallTool( self, env ):
        self._callExternal( [ env['pipBin'], 'uninstall', '-q', 'setuptools' ] )
        self._have_tool = False

    def onBuild( self, config ):
        pythonBin = config['env']['pythonBin']
        self._callExternal( [ pythonBin, 'setup.py', 'sdist', 'bdist_wheel' ] )
    
    