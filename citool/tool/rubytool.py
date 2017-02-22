
from citool.subtool import SubTool

class rubyTool( SubTool ):
    RUBY_VER = 'ruby'

    def getType( self ):
        return self.TYPE_RUNTIME
    
    def getDeps( self ) :
        return [ 'rvm' ]

    def _installTool( self, env ):
        self._buildDeps()
        self._callExternal([
            env['rvmBin'], 'install', env['rubyVer'], '--autolibs=read-only'
        ])
        self._callExternal([
            env['rvmBin'], 'cleanup', 'all'
        ])

    def updateTool( self, env ):
        self._installTool( env )
        
    def uninstallTool( self, env ):
        self._callExternal([
            env['rvmBin'], 'uninstall', env['rubyVer']
        ])
        self._have_tool = False

    def _envNames( self ) :
        return ['rubyVer', 'rubyBin' ]

    def initEnv( self, env ) :
        ruby_ver = env.setdefault('rubyVer', self.RUBY_VER)

        rvm_dir = env['rvmDir']
        bash_bin = env['bashBin']

        try:
            env_to_set = self._callExternal(
                [ bash_bin,  '--noprofile', '--norc', '-c',
                'source {0}/scripts/rvm && \
                rvm use {1} >/dev/null && \
                env | grep "rvm"'.format(rvm_dir, ruby_ver) ],
                verbose = False
            )
        except:
            return

        if env_to_set :
            self.updateEnvFromOutput(env_to_set)
            SubTool.initEnv( self, env )
            
    def _buildDeps( self ):
        self.require_deb([
            'build-essential',
            'gawk',
            'libssl-dev',
            'make',
            'libc6-dev',
            'zlib1g-dev',
            'libyaml-dev',
            'libsqlite3-dev',
            'sqlite3',
            'autoconf',
            'libgmp-dev',
            'libgdbm-dev',
            'libncurses5-dev',
            'automake',
            'libtool',
            'bison',
            'pkg-config',
            'libffi-dev',
            'libgmp-dev',
            'libreadline6-dev',
        ])
