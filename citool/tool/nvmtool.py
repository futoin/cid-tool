
from citool.subtool import SubTool

class nvmTool( SubTool ):
    "Node Version Manager"
    def getType( self ):
        return self.TYPE_RUNENV
