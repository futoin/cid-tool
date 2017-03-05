
import os

from ..buildtool import BuildTool

class setuptoolsTool( BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'setup.py' ]
        )
    
    def getDeps( self ) :
        return [ 'python', 'pip', 'virtualenv' ]
    
    def _installTool( self, env ):
        self._callExternal( [ env['pipBin'], 'install', '-q', 'setuptools' ] )
        
    def updateTool( self, env ):
        self._callExternal( [ env['pipBin'], 'install', '-q', '--upgrade', 'setuptools' ] )
        
    def uninstallTool( self, env ):
        pass
        
    def initEnv( self, env ):
        virtualenv_dir = env['virtualenvDir']
        self._have_tool = os.path.exists(os.path.join(virtualenv_dir, 'bin', 'easy_install'))

    def onBuild( self, config ):
        for d in ['build', 'dist']:
            if os.path.exists(d):
                self._rmTree(d)

        env = config['env']
        pythonBin = env['pythonBin']

        self._callExternal( [ env['pipBin'], 'install', '-q', 'docutils' ] )
        self._callExternal( [ pythonBin, 'setup.py', 'check', '-mr' ] )

        self._callExternal( [ pythonBin, 'setup.py', 'sdist', 'bdist_wheel' ] )
    
    