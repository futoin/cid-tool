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

from __future__ import print_function, absolute_import

from .cid_utbase import cid_UTBase
from futoin.cid.rmstool import RmsTool

import os, stat
import subprocess
import glob

from collections import OrderedDict

class cid_initcmd_Test ( cid_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'initcmd')
    
    def setUp(self):
        self.setUpClass()
        
        os.mkdir(self.TEST_DIR)
        os.chdir(self.TEST_DIR)
            
    def test10_init(self):
        self._call_cid(['init'])
        cfg = self._readJSON('futoin.json')
        
        self.assertEquals(cfg, OrderedDict([
            ('name', 'initcmd')
        ]))
    
    def test11_init_name(self):
        self._call_cid(['init', 'some_name'])
        cfg = self._readJSON('futoin.json')
        
        self.assertEquals(cfg, OrderedDict([
            ('name', 'some_name')
        ]))
        
    def test12_init_vcs_npm(self):
        self._writeJSON('package.json', {
            "name": "futoin-cid-grunt-test",
            "version" : "0.0.1",
            "description": "Futoin CID grunt Test",
            "devDependencies": {
                "grunt": "*"
            },
        })
        
        self._call_cid(['init', '--vcsRepo=git:someRepo.git'])
        cfg = self._readJSON('futoin.json')
        
        self.assertEquals(cfg, OrderedDict([
            ('name', 'futoin-cid-grunt-test'),
            ('version', '0.0.1'),
            ('vcs', 'git'),
            ('vcsRepo', 'someRepo.git'),
        ]))

    
