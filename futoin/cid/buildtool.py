#
# Copyright 2015-2017 (c) Andrey Galkin
#


from .subtool import SubTool

__all__ = ['BuildTool']


class BuildTool(SubTool):
    __slots__ = ()

    def onPrepare(self, config):
        pass

    def onBuild(self, config):
        pass

    def onPackage(self, config):
        pass
