
from .citool_tools_test import citool_Tool_UTBase
import os, re

class cid_UTBase(citool_Tool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpClass(cls):
        cls.TOOL_NAME = re.match(r'^cid_(.+)_Test$', cls.__name__).group(1)
        super(cid_UTBase, cls).setUpClass()
        cls.setUpTool()

    @classmethod
    def setUpTool(cls):
        pass

class cid_bower_Test(cid_UTBase):
    @classmethod
    def setUpTool(cls):
        cls._writeJSON('bower.json', {
            "name": "cid-bower-test",
            "description": "Futoin CID Bower Test",
            "dependencies": {
                "get-size": "~1.2.2"
            },
            "devDependencies": {
                "qunit": "~1.16.0"
            },
        })
        
    def test_prepare( self ):
        self._call_citool( [ 'tool', 'prepare', self.TOOL_NAME ] )
        assert os.path.exists('bower_components/get-size')
        assert os.path.exists('bower_components/qunit')

    def test_package( self ):
        self._call_citool( [ 'tool', 'package', self.TOOL_NAME ] )
        assert os.path.exists('bower_components/get-size')
        assert not os.path.exists('bower_components/qunit')

class cid_bundler_Test(cid_UTBase):
    pass

class cid_cmake_Test(cid_UTBase):
    pass

class cid_composer_Test(cid_UTBase):
    pass

class cid_gem_Test(cid_UTBase):
    pass

class cid_grunt_Test(cid_UTBase):
    pass

class cid_gulp_Test(cid_UTBase):
    pass

class cid_make_Test(cid_UTBase):
    pass

class cid_npm_Test(citool_Tool_UTBase):
    cid_UTBase

class cid_pip_Test(cid_UTBase):
    pass

class cid_puppet_Test(cid_UTBase):
    pass

class cid_setuptools_Test(cid_UTBase):
    pass