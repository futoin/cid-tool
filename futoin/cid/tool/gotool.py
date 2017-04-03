from ..runtimetool import RuntimeTool
from .bashtoolmixin import BashToolMixIn

class goTool( BashToolMixIn, RuntimeTool ):
    """The Go Programming Language
    
Home: https://golang.org/

All versions are installed through GVM.

Only binary releases of Golang are supported for installation
through CID, but you can install source releases through
"cid tool exec gvm -- install sourcetag".
"""
    def getDeps( self ) :
        return [ 'gvm', 'bash', 'binutils', 'gcc' ]
    
    def _installTool( self, env ):
        # in case GVM is already installed without these deps
        self._requireDeb(['bison', 'build-essential'])
        self._requireRpm(['bison', 'glibc-devel'])
        self._requireEmergeDepsOnly(['dev-lang/go'])
        self._requirePacman(['bison', 'glibc',])
        self._requireHomebrew('bison')

        self._callBash( env,
            'source {0} && gvm install {1} --binary'
            .format(env['gvmInit'], env['goVer'])
        )

    def updateTool( self, env ):
        self._installTool( env )
        
    def uninstallTool( self, env ):
        self._callBash( env,
            'source {0} && gvm uninstall {1}'
            .format(env['gvmInit'], env['goVer'])
        )
        self._have_tool = False

    def envNames( self ) :
        return ['goVer', 'goBin' ]

    def initEnv( self, env ) :
        if 'goVer' not in env:
            try:
                env['goVer'] = self._callBash( env,
                    'source {0} && gvm listall | egrep "go[0-9]\.[0-9]+(\.[0-9]+)?$" | sort -rV'
                    .format(env['gvmInit']),
                    verbose=False
                ).split("\n")[0].strip()
            except:
                return
            
        ver = env['goVer']

        try:
            env_to_set = self._callBash( env,
                'source {0} && \
                gvm use {1} >/dev/null && \
                env | egrep -i "(gvm|golang)"'.format(env['gvmInit'], ver),
                verbose = False
            )
        except:
            return

        if env_to_set :
            self._updateEnvFromOutput(env_to_set)
            super(goTool, self).initEnv( env )
    
            
    def onRun( self, config, file, args, tune ):
        env = config['env']
        self._callInteractive([
            env[self._name + 'Bin'], 'run', file
        ] + args)
            
   