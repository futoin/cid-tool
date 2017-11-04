#
# Copyright 2015-2017 (c) Andrey Galkin
#


from ..buildtool import BuildTool
from .npmtoolmixin import NpmToolMixIn


class gulpTool(NpmToolMixIn, BuildTool):
    """Automate and enhance your workflow (Node.js).

Home: http://gulpjs.com/    
"""
    __slots__ = ()

    def autoDetectFiles(self):
        return 'gulpfile.js'

    def onBuild(self, config):
        cmd = [config['env']['gulpBin']]
        self._executil.callMeaningful(cmd)
