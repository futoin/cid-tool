
from .citool_utbase import citool_UTBase
import os, subprocess

class citool_Tool_UTBase ( citool_UTBase ) :
    __test__ = False
    TOOL_NAME = 'invalid'
    TOOL_ENV = {}
    _env_backup = None

    @classmethod
    def setUpClass( cls ):
        cls._env_backup = {}
        cls.TEST_DIR = os.path.join(cls.TEST_RUN_DIR, 'tool_'+cls.TOOL_NAME)
        super(citool_Tool_UTBase, cls).setUpClass()
        os.mkdir( cls.TEST_DIR )
        os.chdir( cls.TEST_DIR )
        
        for k, v in cls.TOOL_ENV.items():
            cls._env_backup[k] = os.environ.get(k, None)
            os.environ[k] = v
            
    @classmethod
    def tearDownClass( cls ):
        for k, v in cls._env_backup.items():
            if v:
                os.environ[k] = v
            else:
                del os.environ[k]

class citool_Tool_UTCommon ( citool_Tool_UTBase ) :
    TOOL_MANAGED = True
    
    def test_10_tool_uninstall( self ):
        if self.TOOL_MANAGED:
            self._call_citool( [ 'tool', 'uninstall', self.TOOL_NAME ] )
        
    def test_20_tool_test( self ):
        if self.TOOL_MANAGED:
            try:
                self._call_citool( [ 'tool', 'test', self.TOOL_NAME ] )
            except:
                return
            raise RuntimeError('Tool must not be present')

    def test_30_tool_install( self ):
        self._call_citool( [ 'tool', 'install', self.TOOL_NAME ] )

    def test_40_tool_test( self ):
        self._call_citool( [ 'tool', 'test', self.TOOL_NAME ] )

    def test_50_tool_update( self ):
        self._call_citool( [ 'tool', 'update', self.TOOL_NAME ] )
        
    def test_60_tool_env( self ):
        self._call_citool( [ 'tool', 'env', self.TOOL_NAME ] )
        # TODO: better test output

# 10
#-----
for t in ['bash', 'curl', 'git', 'hg', 'svn', 'gpg', 'scp', 'ssh', 'make', 'cmake', 'jre', 'jdk']:
    cls = 'citool_Tool_10_' + t
    globals()[cls] = type(cls, (citool_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
        'TOOL_MANAGED' : False,
    })

# Auto-detect system Java after default is run
class citool_Tool_JVMBase(citool_Tool_UTBase):
    @classmethod
    def setUpClass( cls ):
        java_ver=subprocess.check_output(['java', '-version'])

        if java_ver.find('1.8.0'):
            java_ver='8'
        else :
            java_ver='7'
            
        cls.TOOL_ENV = { t + 'Ver': java_ver }
        supet(citool_Tool_JVMBase, cls).setUpClass()


for t in ['jre', 'jdk']:
    cls = 'citool_Tool_11_' + t
    globals()[cls] = type(cls, (citool_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
        'TOOL_MANAGED' : False,
    })

    
# 20
#-----
for t in ['nvm', 'rvm', 'phpbuild']:
    cls = 'citool_Tool_20_' + t
    globals()[cls] = type(cls, (citool_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
    })

# 30
#-----
for t in ['node']: # python
    cls = 'citool_Tool_30_' + t
    globals()[cls] = type(cls, (citool_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
    })
    
mixed_tools = {
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
}
        
if os.environ.get('CIDTEST_NO_COMPILE', '0') != '1':
    mixed_tools.update({
        'php' : { 'ver': '7' },
        'ruby' : { 'ver': 'ruby-2' },
    })
    
for t, ti in mixed_tools.items():
    cls = "citool_Tool_31_{0}".format(t)
    tenv = ti.get('env', {})
    if 'ver' in ti:
        tenv[ "{0}Ver".format(t) ] = ti['ver']
    globals()[cls] = type(cls, (citool_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
        'TOOL_ENV': tenv,
        'TOOL_MANAGED' : ti.get('managed', True),
    })
    #--
    cls = "citool_Tool_30_{0}_system".format(t)
    globals()[cls] = type(cls, (citool_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
        'TOOL_MANAGED' : False,
    })

# 40
#-----
for t in ['npm', 'gem', 'setuptools']:
    cls = 'citool_Tool_40_' + t
    globals()[cls] = type(cls, (citool_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
        'TOOL_MANAGED' : False,
    })

# 50
#-----
os.environ['dockerBin'] = '/bin/true'
for t in ['composer', 'bundler', 'dockercompose']:
    cls = 'citool_Tool_50_' + t
    globals()[cls] = type(cls, (citool_Tool_UTCommon, ), {
        '__test__' : True,
        'TOOL_NAME' : t,
    })
