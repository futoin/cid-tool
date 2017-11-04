#
# Copyright 2015-2017 (c) Andrey Galkin
#


from .subtool import SubTool

__all__ = ['MigrationTool']


class MigrationTool(SubTool):
    __slots__ = ()

    def onMigrate(self, config):
        pass
