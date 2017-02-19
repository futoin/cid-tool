
from citool.subtool import SubTool

import os

class rvmTool( SubTool ):
    "Ruby Version Manager"
    
    RVM_DIR_DEFAULT = os.path.join(os.environ['HOME'], '.rvm')
    RVM_LATEST = 'stable'
    RVM_GPG_KEY = '409B6B1796C275462A1703113804BB82D39DC0E3'
    RVM_GET = 'https://get.rvm.io'

    def getType( self ):
        return self.TYPE_RUNENV

    def getDeps( self ) :
        return [ 'bash', 'curl', 'gpg' ]

    def _installTool( self, env ):
        rvm_dir = env['rvmDir']
        bash_bin = env['bashBin']
        rvm_ver = env.get('rvmVer', self.RVM_LATEST) 
        rvm_get = env.get('rvmGet', self.RVM_GET) 
        rvm_gpg_key = env.get('rvmGpgKey', self.RVM_GPG_KEY)
        
        self._callExternal([
            env['gpgBin'], '--keyserver', env['gpgKeyServer'],
            '--recv-keys', rvm_gpg_key
        ])

        self._callExternal(
            [ bash_bin,  '--noprofile', '--norc', '-c',
              '{0} -sSL {1} | {2} -s {3}'
               .format(env['curlBin'], rvm_get, bash_bin, rvm_ver) ] )
            
    def updateTool( self, env ):
        rvm_bin = env['rvmBin']
        rvm_ver = env.get('rvmVer', self.RVM_LATEST) 
        self._callExternal([ rvm_bin, 'get', rvm_ver ])

    def initEnv( self, env ) :
        rvm_dir = env.setdefault('rvmDir', self.RVM_DIR_DEFAULT)
        rvm_bin_dir = os.path.join(rvm_dir, 'bin')
        rvm_bin = env.setdefault('rvmBin', os.path.join(rvm_bin_dir, 'rvm'))
        self._have_tool = os.path.exists(rvm_bin)
