
from ..buildtool import BuildTool
from .piptoolmixin import PipToolMixIn


class cidTool( PipToolMixIn, BuildTool ):
    "Noop FutoIn-CID - a workaround to allow CID use from virtualenv"

    def _pipName( self ):
        return 'futoin-cid'
