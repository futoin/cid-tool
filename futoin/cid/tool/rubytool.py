
from ..runtimetool import RuntimeTool
from .bashtoolmixin import BashToolMixIn

class rubyTool( BashToolMixIn, RuntimeTool ):
    """Ruby is a dynamic, open source programming language.
    
Home: https://www.ruby-lang.org/en/

System Ruby is used by default.
If rubyVer is set then RVM is used to setup custom rubies.
That may lead to long time and resource consumption due to compilation,
if binary versions are not found for specific system.
"""
    def getDeps( self ) :
        return [ 'rvm' ]

    def _installTool( self, env ):
        ruby_ver = env['rubyVer']
        
        if ruby_ver == self.SYSTEM_VER:
            self._systemDeps()
            return
        
        self._buildDeps()
        self._callExternal([
            env['rvmBin'], 'install', ruby_ver, '--autolibs=read-only'
        ])
        self._callExternal([
            env['rvmBin'], 'cleanup', 'all'
        ])

    def updateTool( self, env ):
        if env['rubyVer'] != self.SYSTEM_VER:
            self._installTool( env )
        
    def uninstallTool( self, env ):
        ruby_ver = env['rubyVer']
        
        if ruby_ver != self.SYSTEM_VER:
            self._callExternal([
                env['rvmBin'], 'uninstall', env['rubyVer']
            ])
            self._have_tool = False

    def envNames( self ) :
        return ['rubyVer', 'rubyBin' ]

    def initEnv( self, env ) :
        ruby_ver = env.setdefault('rubyVer', self.SYSTEM_VER)

        rvm_dir = env['rvmDir']

        try:
            env_to_set = self._callBash( env,
                'source {0} && \
                rvm use {1} >/dev/null && \
                env | grep "rvm"'.format(env['rvmInit'], ruby_ver),
                verbose = False
            )
        except:
            return

        if env_to_set :
            self._updateEnvFromOutput(env_to_set)
            super(rubyTool, self).initEnv( env )
            
    def _buildDeps( self ):
        # APT
        #---
        self._requireDeb([
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
            'libreadline-dev',
        ])
        

        # Extra repo before the rest
        #---
        self._requireYum(['epel-release'])

        self._requireRpm([
            'binutils',
            'patch',
            'libyaml-devel',
            'autoconf',
            'gcc',
            'gcc-c++',
            'glibc-devel',
            'readline-devel',
            'zlib-devel',
            'libffi-devel',
            'openssl-devel',
            'automake',
            'libtool',
            'bison',
            'sqlite-devel',
            'make',
            'm4',
            'gdbm-devel',
            'libopenssl-devel',
            'sqlite3-devel',
        ])
        
        self._requireEmergeDepsOnly(['dev-lang/ruby'])
        self._requirePacman(['ruby'])
        
    def _systemDeps( self ):
        self._requirePackages(['ruby'])
        self._requireEmerge(['dev-lang/ruby'])
        self._requirePacman(['ruby'])
