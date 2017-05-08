
from ..buildtool import BuildTool
from .npmtoolmixin import NpmToolMixIn


class gruntTool(NpmToolMixIn, BuildTool):
    """Grunt: The JavaScript Task Runner.

Home: https://gruntjs.com/    
"""

    def autoDetectFiles(self):
        return ['Gruntfile.js', 'Gruntfile.coffee']

    def _npmName(self):
        return 'grunt-cli'

    def onBuild(self, config):
        gruntBin = config['env']['gruntBin']
        self._callExternal([gruntBin])
