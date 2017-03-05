
class BashToolMixIn( object ):
    def getDeps( self ) :
        return [ 'bash' ]
    
    def _callBash( self, env, cmd, *args, **nargs ):
        return self._callExternal([
            env['bashBin'],
            '--noprofile', '--norc',
            '-c', cmd,
        ], *args, **nargs )
