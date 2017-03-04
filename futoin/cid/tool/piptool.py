
import os

from ..buildtool import BuildTool

class pipTool( BuildTool ):
    REQUIREMENTS_FILE = 'requirements.txt'

    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ self.REQUIREMENTS_FILE ]
        )
    
    def getDeps( self ) :
        return [ 'python', 'virtualenv' ]

    def _envNames( self ) :
        return ['pipBin', 'pipVer']

    def _installTool( self, env ):
        if os.path.exists( env['pipBin'] ):
            self.updateTool( env )
        else:
            self._callExternal([
                os.path.join( env['virtualenvDir'], 'bin', 'easy_install' ), 'pip'
            ])

    def updateTool( self, env ):
        self._callExternal([
            env['pipBin'], 'install', '-q',
            '--upgrade',
            'pip>={0}'.format(env['pipVer']),
        ])
        
    def uninstallTool( self, env ):
        pass
    
    def initEnv( self, env ) :
        pipBin = os.path.join( env['virtualenvDir'], 'bin', 'pip' )
        pipBin = env.setdefault( 'pipBin', pipBin )
        pipVer = env.setdefault( 'pipVer', '9.0.1' )
        
        if os.path.exists( pipBin ):
            pipFactVer = self._callExternal([ pipBin, '--version' ], verbose=False)
            pipFactVer = [int(v) for v in pipFactVer.split(' ')[1].split('.')]
            pipNeedVer = [int(v) for v in pipVer.split('.')]
            
            self._have_tool = pipNeedVer <= pipFactVer
    
    def onPrepare( self, config ):
        if os.path.exists(self.REQUIREMENTS_FILE):
            self._callExternal( [ config['env']['pipBin'], 'install', '-r', self.REQUIREMENTS_FILE ] )
