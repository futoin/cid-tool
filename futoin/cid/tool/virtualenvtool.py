
import os

from ..runenvtool import RunEnvTool
from .bashtoolmixin import BashToolMixIn

class virtualenvTool( BashToolMixIn, RunEnvTool ):
    def getDeps( self ) :
        return [ 'bash', 'python' ]
    
    def getPostDeps( self ) :
        # we need to ensure that if cid is called from virtualenv env
        # it's still can be used
        # So, CID can be in system and in each virtualenv as well
        return ['cid']
    
    def _envNames( self ) :
        return [ 'virtualenvDir', 'virtualenvVer']
    
    def _installTool( self, env ):
        python_ver = env['pythonVer'].split('.')
        
        virtualenv_dir = env['virtualenvDir']
        
        # virtualenv depends on ensurepip and provides no setuptools
        # ensurepip is not packaged on all OSes...
        if False and int(python_ver[0]) == 3 and int(python_ver[1]) >= 3:
            self._callExternal([
                env['pythonRawBin'],
                '-m', 'venv',
                '--system-site-packages',
                '--symlinks',
                '--without-pip', # avoid ensurepip run
                '--clear',
                virtualenv_dir
            ])
        else:
            # Looks quite stupid, but it's a workaround for different OSes
            pip = self._which('pip')
            
            if not pip:
                self._requirePackages(['python-virtualenv'])
                self._requireEmerge(['dev-python/virtualenv'])
                self._requirePacman(['python-virtualenv'])
                
                self._requireDeb(['python-pip'])
                self._requireYum(['python2-pip'])
                self._requireEmerge(['dev-python/pip'])
                self._requirePacman(['python-pip'])
                
                pip = self._which('pip')
                
            if pip:
                self._trySudoCall([ pip, 'install', '-q', '--upgrade', 'virtualenv>={0}'.format(env['virtualenvVer']) ])
            
            virtualenv = self._which('virtualenv')
            
            if not virtualenv:
                raise RuntimeError('Failed to find virtualenv')

            self._callExternal([
                virtualenv,
                '--python={0}'.format(env['pythonRawBin']),
                '--clear',
                virtualenv_dir
            ])
            
    def updateTool( self, env ):
        pass
    
    def initEnv( self, env ) :
        virtualenv_dir = '.virtualenv-{0}'.format(env['pythonVer'][:3])
        virtualenv_dir = env.setdefault('virtualenvDir', os.path.join(os.environ['HOME'], virtualenv_dir))
        
        env.setdefault('virtualenvVer', '15.1.0')
        
        self._have_tool = os.path.exists(os.path.join(virtualenv_dir, 'bin', 'activate'))
        
        if self._have_tool:
            env_to_set = self._callBash( env,
                'source {0}/bin/activate && env | grep \'{0}\''.format(virtualenv_dir),
                verbose = False
            )
                
            self._updateEnvFromOutput(env_to_set)
            # reverse-dep hack
            env['pythonBin'] = os.path.join(virtualenv_dir, 'bin', 'python')

