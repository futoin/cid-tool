#
# Copyright 2015-2019 Andrey Galkin <andrey@futoin.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from .cid_utbase import cid_Tool_UTBase
import os, subprocess, sys
import platform, re
from nose.plugins.attrib import attr
from futoin.cid.util import detect

IS_LINUX = cid_Tool_UTBase.IS_LINUX
IS_MACOS = cid_Tool_UTBase.IS_MACOS
is_alpinelinux = os.path.exists('/etc/alpine-release')

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
        res = self._call_cid( [ 'tool', 'env', self.TOOL_NAME ], retout=True )
        
        vars = {}
        for l in res.split("\n"):
            if l:
                n, v = l.split('=', 1)
                vars[n] = v
        
        ver_var = self.TOOL_NAME + 'Ver'
        
        if ver_var in self.TOOL_ENV:
            tool_ver = self.TOOL_ENV[ver_var]
            
            if not vars[ver_var].startswith("'{0}".format(tool_ver)):
                self.assertEqual(vars[ver_var], "'{0}'".format(tool_ver))
            
            del os.environ[ver_var]
            
            res2 = self._call_cid( [ 'tool', 'env', self.TOOL_NAME, tool_ver ], retout=True )
            
            os.environ[ver_var] = tool_ver
            self.assertEqual(res, res2)
            
    def test_70_tool_ver( self ):
        tool_name = self.TOOL_NAME
        
        ver_var = tool_name + 'Ver'
        
        if ver_var not in self.TOOL_ENV:
            return

        tool_ver = self.TOOL_ENV[ver_var]
        
        if tool_name in ('php', 'phpfpm'):
            res = self._call_cid( [ 'tool', 'exec', tool_name, '--', '--version' ], retout=True )
            req = "PHP {0}".format(tool_ver)
        elif tool_name == 'ruby':
            res = self._call_cid( [ 'tool', 'exec', tool_name, '--', '--version' ], retout=True )
            req = "ruby {0}".format(tool_ver)
        elif tool_name == 'java':
            res = self._call_cid( [ 'tool', 'exec', tool_name, '--', '-version' ],
                                 retout=True, merge_stderr=True )
            
            req = '"1.{0}.[0-9_]+"'.format(tool_ver)
            
            if re.search(req, res):
                return
        elif tool_name == 'liquibase':
            res = self._call_cid([ 'tool', 'exec', tool_name, '--', '--version' ],
                                 retout=True, merge_stderr=True )
            res = res.split('\n')[1]
            req = "Liquibase Version: {0}".format(tool_ver)
            
        elif tool_name == 'flyway':
            res = self._call_cid([ 'tool', 'exec', tool_name ],
                                 retout=True, merge_stderr=True )
            res = res.split('\n')[1]
            req = "Flyway {0}".format(tool_ver)
            
        else:
            return 
        
        if not res.startswith(req):
            self.assertEqual(req, res)

    def test_71_tool_envexec( self ):
        tool_name = self.TOOL_NAME
        
        ver_var = tool_name + 'Ver'
        
        if ver_var not in self.TOOL_ENV:
            return

        tool_ver = self.TOOL_ENV[ver_var]
        
        if tool_name in ('php', 'phpfpm'):
            tool_bin = tool_name == 'phpfpm' and 'php-fpm' or 'php'
            res = self._call_cid( [ 'tool', 'exec', tool_name, '--', '--version' ], retout=True )
            res2 = self._call_cid( [ 'tool', 'envexec', tool_name, '--', tool_bin, '--version' ], retout=True )
        elif tool_name == 'ruby':
            res = self._call_cid( [ 'tool', 'exec', tool_name, '--', '--version' ], retout=True )
            res2 = self._call_cid( [ 'tool', 'envexec', tool_name, '--', tool_name, '--version' ], retout=True )
        elif tool_name == 'java':
            res = self._call_cid( [ 'tool', 'exec', tool_name, '--', '-version' ],
                                 retout=True, merge_stderr=True )
            res2 = self._call_cid( [ 'tool', 'envexec', tool_name, '--', tool_name, '-version' ],
                                 retout=True, merge_stderr=True )
            res = res.split("\n")[1]
            res2 = res2.split("\n")[1]
        else:
            return 
        
        self.assertEqual(res, res2)

# 10
#-----
system_tools = [
    'bash',
    'curl',
    'git',
    'hg',
    'svn',
    'gpg',
    'scp',
    'ssh',
    'make',
    'cmake',
    'tar',
    'unzip',
    'gcc',
    'binutils',
    'nginx',
    'bzip2',
    'gzip',
    'xz',
    'rust',
    'docker',
]

if not cid_Tool_UTBase.IS_LINUX:
    system_tools.remove('docker')
if is_alpinelinux:
    system_tools.remove('rust')

for t in system_tools:
    cls = 'cid_Tool_10_' + t
    clstype = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
        'TOOL_MANAGED' : False,
    })
    globals()[cls] = attr(tool=t)(clstype)

    
# 20
#-----
managed_tools = [
    'nvm',
    'rvm',
    'phpbuild',
    'sdkman',
    'ant',
    'gradle',
    'maven',
    'sbt',
    'scala',
    'gvm',
    'jfrog',
    'rustup',
]

if is_alpinelinux:
    managed_tools.remove('rustup')

for t in managed_tools:
    cls = 'cid_Tool_20_' + t
    clstype = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
    })
    globals()[cls] = attr(tool=t)(clstype)
    
if IS_MACOS:
    cid_Tool_20_jfrog.TOOL_MANAGED = False  # pylint: disable=undefined-variable

# 30
#-----
for t in ['node', 'go']:
    cls = 'cid_Tool_30_' + t
    clstype = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
    })
    globals()[cls] = attr(tool=t)(clstype)
    
mixed_tools = {
    'java': {
        'ver': '7',
        'managed': False,
    },
    'jdk': {
        'ver': '8',
        'managed': False,
    },
    'liquibase' : {
        'ver': '3.4.2',
    },
    'flyway' : {
        'ver': '4.1.2',
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
            'scl': ['5.6', '7.0', '7.1'],
            'brew' : ['5.6', '7.0', '7.1']
        },
        'src': {
            'env': {
                'phpVer': '7.2',
                'phpForceBuild': '1',
            }
        }
    },
    'phpfpm' : {
        'managed': False,
        'binver': {
            'deb': ['5.6', '7.0', '7.1'],
            'scl': ['5.6', '7.0', '7.1'],
            'brew' : ['5.6', '7.0', '7.1']
        },
    },
    'ruby' : {
        'managed': False,
        'binver': {
            'deb': ['1.9', '2.0', '2.1', '2.2', '2.3', '2.4', '2.5', '2.6'],
            'scl': ['1.9', '2.0', '2.2', '2.3', '2.4', '2.5'],
            'brew' : ['1.8', '1.9', '2.1', '2.2', '2.3', '2.4', '2.5', '2.6']
        },
        'src': {
            'env': {
                'rubyVer': '2.4',
                'rubyForceBuild': '1',
            }
        }
    },
    'rust' : {
        'ver': '1.8.0',
    }
}
    
if is_alpinelinux:
    del mixed_tools['rust']

if detect.isSLES():
    del mixed_tools['php']['src']
    
for t, ti in mixed_tools.items():
    cls = "cid_Tool_31_{0}".format(t)
    tenv = ti.get('env', {})
    if 'ver' in ti:
        tenv[ "{0}Ver".format(t) ] = ti['ver']
    clstype = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
        'TOOL_ENV': tenv,
        'TOOL_MANAGED' : ti.get('managed', True),
    })
    globals()[cls] = attr(tool=t)(clstype)
    #--
    cls = "cid_Tool_30_{0}_system".format(t)
    clstype = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
        'TOOL_MANAGED' : False,
    })
    globals()[cls] = attr(tool=t)(clstype)
    
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
                clstype = type(cls, (cid_Tool_UTCommon, ), {
                    '__test__' : True,
                    'TOOL_NAME' : t,
                    'TOOL_ENV': tenv,
                    'TOOL_MANAGED' : False,
                })
                globals()[cls] = attr(tool=t)(clstype)

        if 'scl' in binver and (
            linux_distro[0].startswith('CentOS') or
            linux_distro[0].startswith('Red Hat') or
            linux_distro[0].startswith('Oracle')
            ):
            for bv in binver['scl']:
                cls = "cid_Tool_32_{0}_scl_{1}".format(t, bv.replace('.', ''))
                tenv = {}
                tenv[ "{0}Ver".format(t) ] = bv
                clstype = type(cls, (cid_Tool_UTCommon, ), {
                    '__test__' : True,
                    'TOOL_NAME' : t,
                    'TOOL_ENV': tenv,
                    'TOOL_MANAGED' : False,
                })
                globals()[cls] = attr(tool=t)(clstype)

        if 'brew' in binver and cid_Tool_UTBase.IS_MACOS:
            for bv in binver['brew']:
                cls = "cid_Tool_32_{0}_brew_{1}".format(t, bv.replace('.', ''))
                tenv = {}
                tenv[ "{0}Ver".format(t) ] = bv
                clstype = type(cls, (cid_Tool_UTCommon, ), {
                    '__test__' : True,
                    'TOOL_NAME' : t,
                    'TOOL_ENV': tenv,
                    'TOOL_MANAGED' : False,
                })
                globals()[cls] = attr(tool=t)(clstype)
                
    if 'src' in ti and cid_Tool_UTBase.ALLOW_SRC_BUILDS:
        #--
        cls = "cid_Tool_33_{0}_srcbuild".format(t)
        clstype = type(cls, (cid_Tool_UTCommon, ), {
            '__test__' : True,
            'TOOL_NAME' : t,
            'TOOL_ENV': ti['src']['env'],
        })
        globals()[cls] = attr(tool=t)(clstype)

# 40 - unmanaged
#-----
tools_umanaged = [
    'npm',
    'gem',
    'setuptools',
]

for t in tools_umanaged:
    cls = 'cid_Tool_40_' + t
    clstype = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
        'TOOL_MANAGED' : False,
    })
    globals()[cls] = attr(tool=t)(clstype)

# 50 - managed
#-----

tools_managed2 = [
    'composer',
    'bundler',
    'dockercompose',
    'twine',
    'uwsgi',
    'webpack',
    'yarn',
]

if not IS_LINUX:
    tools_managed2.remove('dockercompose')

for t in tools_managed2:
    cls = 'cid_Tool_50_' + t
    clstype = type(cls, (cid_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
    })
    globals()[cls] = attr(tool=t)(clstype)
