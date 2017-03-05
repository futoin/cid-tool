
import os

from ..buildtool import BuildTool
from .piptoolmixin import PipToolMixIn

class setuptoolsTool( PipToolMixIn, BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'setup.py' ]
        )
    
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
        self._requirePip( env, 'wheel' )
        self._callExternal( [ env['pythonBin'], 'setup.py', 'sdist', 'bdist_wheel' ] )
    

    def onCheck( self, config ):
        env = config['env']
        self._requirePip( env, 'docutils' )
        self._requirePip( env, 'readme' )
        self._callExternal( [ env['pythonBin'], 'setup.py', 'check', '-mrs' ] )

    