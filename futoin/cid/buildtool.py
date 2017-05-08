
from .subtool import SubTool

__all__ = ['BuildTool']


class BuildTool(SubTool):
    def onPrepare(self, config):
        pass

    def onBuild(self, config):
        pass

    def onPackage(self, config):
        pass
