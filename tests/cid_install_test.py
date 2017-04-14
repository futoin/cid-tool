
from .cid_utbase import cid_Tool_UTBase
import os, subprocess, sys
import platform

class cid_Tool_UTCommon ( cid_Tool_UTBase ) :
    TOOL_MANAGED = True
    
    def test_10_tool_uninstall( self ):
        if self.TOOL_MANAGED:
            self._call_cid( [ 'tool', 'uninstall', self.TOOL_NAME ] )
        
    def test_20_tool_test( self ):
        if self.TOOL_MANAGED:
            try:
                self._call_cid( [ 'tool', 'test', self.TOOL_NAME ], returncode=1 )
            except:
                raise RuntimeError('Tool must not be present')

    def test_30_tool_install( self ):
        self._call_cid( [ 'tool', 'install', self.TOOL_NAME ] )

    def test_40_tool_test( self ):
        self._call_cid( [ 'tool', 'test', self.TOOL_NAME ] )

    def test_50_tool_update( self ):
        self._call_cid( [ 'tool', 'update', self.TOOL_NAME ] )
        
    def test_60_tool_env( self ):
        (r, w) = os.pipe()
        self._call_cid( [ 'tool', 'env', self.TOOL_NAME ], stdout=w )
        res = os.read(r, 4096)
        os.close(r)
        os.close(w)
        
        try: res = str(res, 'utf8')
        except: pass
        
        vars = {}
        for l in res.split("\n"):
            if l:
                n, v = l.split('=')
                vars[n] = v
        
        ver_var = self.TOOL_NAME + 'Ver'
        
        if ver_var in self.TOOL_ENV:
            tool_ver = self.TOOL_ENV[ver_var]
            self.assertEqual(vars[ver_var], "'{0}'".format(tool_ver))
            
            del os.environ[ver_var]
            
            (r, w) = os.pipe()
            self._call_cid( [ 'tool', 'env', self.TOOL_NAME, tool_ver ], stdout=w )
            res2 = os.read(r, 4096)
            os.close(r)
            os.close(w)
            
            os.environ[ver_var] = tool_ver
            
            try: res2 = str(res2, 'utf8')
            except: pass
            
            self.assertEqual(res, res2)

# 10
#-----
for t in ['bash', 'curl', 'git', 'hg', 'svn', 'gpg', 'scp', 'ssh',
          'make', 'cmake', 'tar', 'unzip', 'gcc', 'binutils', 'docker']:
    cls = 'cid_Tool_10_' + t
    globals()[cls] = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
        'TOOL_MANAGED' : False,
    })

    
# 20
#-----
for t in ['nvm', 'rvm', 'phpbuild', 'sdkman', 'ant',
          'gradle', 'maven', 'sbt', 'scala', 'gvm', 'rustup']:
    cls = 'cid_Tool_20_' + t
    globals()[cls] = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
    })

# 30
#-----
for t in ['node', 'go']:
    cls = 'cid_Tool_30_' + t
    globals()[cls] = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
    })
    
mixed_tools = {
    'java': {
        'ver': '7',
        'managed': False,
    },
    'jdk': {
        'ver': '8',
        'managed': False,
    },
    'python' : {
        'ver': '2.7',
        'managed': False,
    },
    'pip' : {
        'env': {
            'pythonVer': '2',
        },
        'managed': False,
    },
    'php' : {
        'managed': False,
        'binver': {
            'deb': ['5.6', '7.0', '7.1'],
            'scl': ['5.6', '7.0'],
        },
    },
    'ruby' : {
        'managed': False,
        'binver': {
            'deb': ['1.8', '1.9', '2.0', '2.1', '2.2', '2.3'],
            'scl': ['1.9', '2.0', '2.2', '2.3'],
        },
    },
    'rust' : {
        'ver': '1.8.0',
    }
}
        
if os.environ.get('CIDTEST_NO_COMPILE', '0') != '1':
    mixed_tools.update({
        'php' : {
            'ver': '7.1',
            'env': {
                'phpBinOnly': '',
            }
        },
        'ruby' : {
            'ver': 'ruby-2.4',
            'env': {
                'rubyBinOnly': '',
            }
        },
    })
    
for t, ti in mixed_tools.items():
    cls = "cid_Tool_31_{0}".format(t)
    tenv = ti.get('env', {})
    if 'ver' in ti:
        tenv[ "{0}Ver".format(t) ] = ti['ver']
    globals()[cls] = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
        'TOOL_ENV': tenv,
        'TOOL_MANAGED' : ti.get('managed', True),
    })
    #--
    cls = "cid_Tool_30_{0}_system".format(t)
    globals()[cls] = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
        'TOOL_MANAGED' : False,
    })
    
    if 'binver' in ti:
        linux_distro = platform.linux_distribution()
        binver = ti['binver']
        
        if 'deb' in binver and (
            linux_distro[0].startswith('debian') or
            linux_distro[0].startswith('Ubuntu')
            ):
            for bv in binver['deb']:
                cls = "cid_Tool_32_{0}_deb_{1}".format(t, bv.replace('.', ''))
                tenv = {}
                tenv[ "{0}Ver".format(t) ] = bv
                globals()[cls] = type(cls, (cid_Tool_UTCommon, ), {
                    '__test__' : True,
                    'TOOL_NAME' : t,
                    'TOOL_ENV': tenv,
                    'TOOL_MANAGED' : False,
                })

        if 'scl' in binver and (
            linux_distro[0].startswith('CentOS') or
            linux_distro[0].startswith('Red Hat') or
            linux_distro[0].startswith('SUSE')
            ):
            for bv in binver['deb']:
                cls = "cid_Tool_32_{0}_scl_{1}".format(t, bv.replace('.', ''))
                tenv = {}
                tenv[ "{0}Ver".format(t) ] = bv
                globals()[cls] = type(cls, (cid_Tool_UTCommon, ), {
                    '__test__' : True,
                    'TOOL_NAME' : t,
                    'TOOL_ENV': tenv,
                    'TOOL_MANAGED' : False,
                })

# 40 - unmanaged
#-----
for t in ['npm', 'gem', 'setuptools']:
    cls = 'cid_Tool_40_' + t
    globals()[cls] = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
        'TOOL_MANAGED' : False,
    })

# 50 - managed
#-----
for t in ['composer', 'bundler', 'dockercompose', 'twine']:
    cls = 'cid_Tool_50_' + t
    globals()[cls] = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
    })
