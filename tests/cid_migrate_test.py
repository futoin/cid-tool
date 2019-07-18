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

    @classmethod
    def setUpTool(cls):
        pass
    

#=============================================================================
@attr(tool='liquibase')
class cid_liquibase_Test(cid_MigrateTool_UTBase):
    __test__ = True

    @classmethod
    def setUpTool(cls):
        cls._writeFile('changelog.sql',
"""--liquibase formatted sql

--changeset test:1 runAlways:true failOnError:true
CREATE TABLE IF NOT EXISTS liquibaseTest(tid int auto_increment primary key);
""")    

    def test_migrate(self):
        self._writeFile('liquibase.properties', """
driver: com.mysql.jdbc.Driver
url: jdbc:mysql://{0}/liquibase
username: liquibase
password: liquibase
changeLogFile: changelog.sql
""".format(self.RMS_HOST))
        self._call_cid(['migrate'])

    def test_migrate_fail(self):
        self._writeFile('liquibase.properties', """
driver: com.mysql.jdbc.Driver
url: jdbc:mysql://{0}/invalid
username: liquibase
password: liquibase
changeLogFile: changelog.sql
""".format(self.RMS_HOST))
        self._call_cid(['migrate'], returncode=1)
        
#=============================================================================
@attr(tool='flyway')
class cid_flyway_Test(cid_MigrateTool_UTBase):
    __test__ = True

    @classmethod
    def setUpTool(cls):
        os.makedirs('sql')
        cls._writeFile('sql/R__test.sql',
"""
CREATE TABLE IF NOT EXISTS flywayTest(tid int auto_increment primary key);
""")    

    def test_migrate(self):
        self._writeFile('flyway.conf', """
flyway.url=jdbc:mysql://{0}/flyway
flyway.user=flyway
flyway.password=flyway
""".format(self.RMS_HOST))
        self._call_cid(['migrate'])

    def test_migrate_fail(self):
        self._writeFile('flyway.conf', """
flyway.url=jdbc:mysql://{0}/invalid
flyway.user=flyway
flyway.password=flyway
""".format(self.RMS_HOST))
        self._call_cid(['migrate'], returncode=1)
