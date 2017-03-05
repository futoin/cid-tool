
import os

from ..runenvtool import RunEnvTool
from .bashtoolmixin import BashToolMixIn

class rvmTool( BashToolMixIn, RunEnvTool ):
    "Ruby Version Manager"
    
    RVM_DIR_DEFAULT = os.path.join(os.environ['HOME'], '.rvm')
    RVM_LATEST = 'stable'
    RVM_GPG_KEY = '409B6B1796C275462A1703113804BB82D39DC0E3'
    RVM_GET = 'https://get.rvm.io'

    def getDeps( self ) :
        return [ 'bash', 'curl', 'gpg' ]

    def _installTool( self, env ):
        rvm_dir = env['rvmDir']
        rvm_get = env.get('rvmGet', self.RVM_GET) 
        rvm_gpg_key = env.get('rvmGpgKey', self.RVM_GPG_KEY)
        
        self._callExternal([
            env['gpgBin'], '--keyserver', env['gpgKeyServer'],
            '--recv-keys', rvm_gpg_key
        ], suppress_fail=True)

        os.environ['rvm_user_install_flag'] = '1'
        os.environ['rvm_auto_dotfiles_flag'] = '0'

        self._callBash( env,
              '{0} -sSL {1} | {2} -s {3} --path {4}'
               .format(env['curlBin'], rvm_get, env['bashBin'], env['rvmVer'], env['rvmDir']) )
            
    def updateTool( self, env ):
        self._callExternal([ env['rvmBin'], 'get', env['rvmVer'] ])
        
    def uninstallTool( self, env ):
        try:
            self._callExternal([ env['rvmBin'], 'implode', '--force' ])
        except:
            pass
        self._callBash( env,
            'chmod -R g+w {0}; rm -rf {0}'
            .format(env['rvmDir']) )
        self._have_tool = False

    def _envNames( self ) :
        return ['rvmVer', 'rvmDir', 'rvmBin', 'rvmGet', 'rvmGpgKey' ]

    def initEnv( self, env ) :
        for v in ['rvm_path', 'rvm_bin_path', 'rvm_prefix', 'rvm_version']:
            try: del os.environ[v]
            except: pass
        
        env.setdefault('rvmVer', self.RVM_LATEST) 
        rvm_dir = env.setdefault('rvmDir', self.RVM_DIR_DEFAULT)
        rvm_bin_dir = os.path.join(rvm_dir, 'bin')
        rvm_bin = env.setdefault('rvmBin', os.path.join(rvm_bin_dir, 'rvm'))
        self._have_tool = os.path.exists(rvm_bin)
