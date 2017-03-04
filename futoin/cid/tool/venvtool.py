
import os

from ..runenvtool import RunEnvTool

class venvTool( RunEnvTool ):
    def getDeps( self ) :
        return [ 'bash', 'python' ]
    
    def _envNames( self ) :
        return [ 'venvDir', 'venvVer']
    
    def _installTool( self, env ):
        python_ver = env['pythonVer'].split('.')
        
        venv_dir = env['venvDir']
        
        # venv depends on ensurepip and provides no setuptools
        # ensurepip is not packaged on all OSes...
        if False and int(python_ver[0]) == 3 and int(python_ver[1]) >= 3:
            self._callExternal([
                env['pythonRawBin'],
                '-m', 'venv',
                '--system-site-packages',
                '--symlinks',
                '--without-pip', # avoid ensurepip run
                '--clear',
                venv_dir
            ])
        else:
            # Looks quite stupid, but it's a workaround for different OSes
            pip = self._which('pip')
            
            if not pip:
                self.requirePackages(['python-virtualenv'])
                pip = self._which('pip')
                
            if pip:
                self._trySudoCall([ pip, 'install', '-q', '--upgrade', 'virtualenv>={0}'.format(env['venvVer']) ])
            
            virtualenv = self._which('virtualenv')

            self._callExternal([
                virtualenv,
                '--python={0}'.format(env['pythonRawBin']),
                '--clear',
                venv_dir
            ])
            
    def updateTool( self, env ):
        pass
    
    def initEnv( self, env ) :
        venv_dir = '.venv-{0}'.format(env['pythonVer'][:3])
        venv_dir = env.setdefault('venvDir', os.path.join(os.environ['HOME'], venv_dir))
        
        env.setdefault('venvVer', '15.1.0')
        
        self._have_tool = os.path.exists(os.path.join(venv_dir, 'bin', 'activate'))
        
        if self._have_tool:
            env_to_set = self._callExternal(
                [ env['bashBin'],  '--noprofile', '--norc', '-c',
                'source {0}/bin/activate && env | grep \'{0}\''.format(venv_dir) ],
                verbose = False
            )
                
            self._updateEnvFromOutput(env_to_set)
            # reverse-dep hack
            env['pythonBin'] = os.path.join(venv_dir, 'bin', 'python')

