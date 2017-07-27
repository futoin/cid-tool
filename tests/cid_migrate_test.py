
from .cid_utbase import cid_Tool_UTBase
from nose.plugins.attrib import attr
import os, re


#=============================================================================
class cid_MigrateTool_UTBase(cid_Tool_UTBase):
    RMS_HOST = os.environ.get('RMS_HOST', '10.11.1.11')
    
    @classmethod
    def setUpClass(cls):
        cls.TOOL_NAME = re.match(r'^cid_(.+)_Test$', cls.__name__).group(1)
        super(cid_MigrateTool_UTBase, cls).setUpClass()
        cls.setUpTool()

#=============================================================================
@attr(tool='liquibase')
class cid_liquibase_Test(cid_MigrateTool_UTBase):
    __test__ = True

    @classmethod
    def setUpTool(cls):
        # TODO:
        jar = 'http://central.maven.org/maven2/mysql/mysql-connector-java/5.1.43/mysql-connector-java-5.1.43.jar'
        cls._call_cid(['tool', 'exec', 'curl', '--', jar, '-o', 'mysql-connector-java.jar'])
    
    def test_migrate(self):
        self._writeFile('changelog.sql',
"""--liquibase formatted sql

--changeset test:1 runAlways:true failOnError:true
CREATE TABLE IF NOT EXISTS liquibaseTest(tid int auto_increment primary key);
""")
        
        self._writeFile('liquibase.properties', """
driver: com.mysql.jdbc.Driver
classpath: mysql-connector-java.jar
url: jdbc:mysql://{0}/liquibase
username: liquibase
password: liquibase
changeLogFile: changelog.sql
""".format(self.RMS_HOST))
        self._call_cid(['migrate'])

    def test_migrate_fail(self):
        self._writeFile('liquibase.properties', """
driver: com.mysql.jdbc.Driver
classpath: mysql-connector-java.jar
url: jdbc:mysql://{0}/invalid
username: liquibase
password: liquibase
changeLogFile: changelog.sql
""".format(self.RMS_HOST))
        self._call_cid(['migrate'], returncode=1)
