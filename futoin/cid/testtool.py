
from .subtool import SubTool

__all__ = ['TestTool']


class TestTool(SubTool):
    __slots__ = ()

    def onCheck(self, config):
        pass
