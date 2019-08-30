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
from nose.plugins.attrib import attr

from .cid_utbase import cid_UTBase
from futoin.cid.rmstool import RmsTool

import os, stat, fcntl
import subprocess
import glob
import shutil

class cid_packagecmd_Test ( cid_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'packagecmd')
    _create_test_dir = True
    
    def setUp( self ):
        shutil.rmtree( self.TEST_DIR )
        os.mkdir(self.TEST_DIR)
        os.chdir(self.TEST_DIR)
        self._goToBase()

    def _test_common(self, compressor, ext):
        cfg = {
            "name": "cid-packagecmd-test",
            "version": "0.0.1",
        }
        if compressor:
            cfg.update({
                "toolTune" : {
                    "tar": {
                        "compressor": compressor,
                    }
                }
            })
            
        self._writeJSON('futoin.json', cfg)
                
        self._call_cid(['package'])

        res = glob.glob('cid-packagecmd-test-CI-0.0.1-*.*')
        self.assertEqual(len(res), 1)
        self.assertEqual(os.path.splitext(res[0])[1], ext)

    def test_tar(self):
        self._test_common('tar', '.tar')

    def test_tgz(self):
        self._test_common('gzip', '.tgz')

    def test_tz2(self):
        self._test_common('bzip2', '.tbz2')

    def test_xz(self):
        self._test_common('xz', '.txz')

    def test_default(self):
        self._test_common(None, '.tgz')
