
from citool.subtool import SubTool

class rubyTool( SubTool ):
    RUBY_VER = 'ruby-2.4'

    def getType( self ):
        return self.TYPE_RUNTIME
    
    def getDeps( self ) :
        return [ 'rvm' ]

    def _installTool( self, env ):
        self._callExternal([
            env['rvmBin'], 'install', env['rubyVer'], '--autolibs=read-only'
        ])
        self._callExternal([
            env['rvmBin'], 'cleanup', 'all'
        ])

    def updateTool( self, env ):
        self._installTool( env )

    def initEnv( self, env ) :
        ruby_ver = env.setdefault('rubyVer', self.RUBY_VER)

        rvm_dir = env['rvmDir']
        bash_bin = env['bashBin']

        try:
            env_to_set = self._callExternal(
                [ bash_bin, '-c',
                'source {0}/scripts/rvm && \
                rvm use {1} >/dev/null && \
                env | grep "rvm"'.format(rvm_dir, ruby_ver) ],
                verbose = False
            )
        except:
            return

        if env_to_set :
            self.updateEnvFromOutput(env_to_set)
            self._have_tool = True