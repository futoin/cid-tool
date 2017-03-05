
from __future__ import print_function

from ..runtimetool import RuntimeTool

class pythonTool( RuntimeTool ):
    VER_CMD = 'import sys; print( sys.version[:3] )'
    
    def getPostDeps( self ) :
        # hackish hack
        return ['virtualenv']
    
    def _envNames( self ) :
        return ['pythonBin', 'pythonVer']
    
    def _installTool( self, env ):
        if int(env['pythonVer'].split('.')[0]) == 3:
            self._requireDeb(['python3'])
            self._requireZypper(['python3'])
            self._requireYum(['epel-release'])
            self._requireYum(['python34'])
        else:
            self._requirePackages(['python'])
    
    def uninstallTool( self, env ):
        pass

    def initEnv( self, env ) :
        python_ver = env.setdefault('pythonVer', '3')
        bin_name = None
        
        if int(python_ver.split('.')[0]) == 3:
            bin_name = 'python3'

        super(pythonTool, self).initEnv( env, bin_name )
        
        if self._have_tool and 'pythonRawBin' not in env:
            env['pythonRawBin'] = env['pythonBin']
            python_ver_fact = self._callExternal(
                [ env['pythonRawBin'], '-c', self.VER_CMD ],
                verbose = False
            ).strip()
            
            if python_ver[:3] > python_ver_fact:
                raise RuntimeError(
                    'Too old python version {0} when {1} is required'
                    .format(python_ver, python_ver_fact)
                )
            env['pythonVer'] = python_ver_fact

