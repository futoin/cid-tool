
import os

from .bashtoolmixin import BashToolMixIn

class SdkmanToolMixIn( BashToolMixIn ):
    def getDeps( self ) :
        return super( SdkmanToolMixIn, self ).getDeps() + [ 'sdkman' ]

    def _sdkName( self ):
        return self._name
    
    def _binName( self ):
        return self._name
    
    def _setAutoAnswer( self, env ):
        self._callBash( env,
            'grep -q "sdkman_auto_answer=true" {0} || echo "sdkman_auto_answer=true" >> {0}'
            .format(os.path.join(env['sdkmanDir'], 'etc', 'config')),
            verbose=False
        )
    
    def _callSdkman( self, env, cmd, verbose=False ):
        return self._callBash( env,
            'source {0} >/dev/null && sdk {1}'.format(
                env['sdkmanInit'],
                cmd
            ),
            verbose=verbose
        )
        
    def _installTool( self, env ):
        self._setAutoAnswer( env )
        self._callSdkman( env,
            'install {0} {1}'.format(
                self._sdkName(),
                env.get(self._name + 'Ver', '')
            )
        )
        
    def updateTool( self, env ):
        self._setAutoAnswer( env )
        self._callSdkman( env,
            'upgrade {0}'.format(
                self._sdkName()
            )
        )

        
    def uninstallTool( self, env ):
        self._setAutoAnswer( env )
        self._callSdkman( env,
            'uninstall {0} {1}'.format(
                self._sdkName(),
                env.get(self._name + 'Ver', '')
            )
        )

    def initEnv( self, env ) :
        try:
            env_to_set = self._callSdkman( env,
                'use {0} >/dev/null && env | grep -i {0}'.format(self._sdkName()),
                verbose = False
            )
        except:
            return

        if env_to_set :
            self._updateEnvFromOutput(env_to_set)
            super(SdkmanToolMixIn, self).initEnv( env, self._binName() )