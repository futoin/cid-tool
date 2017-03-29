
class BashToolMixIn( object ):
    def getDeps( self ) :
        return [ 'bash' ]
    
    def _callBash( self, env, cmd, *args, **nargs ):
        return self._callExternal([
            env['bashBin'],
            '--noprofile', '--norc',
            '-c', cmd,
        ], *args, **nargs )
    
    def _callBashInteractive( self, env, cmd ):
        return self._callInteractive([
            env['bashBin'],
            '--noprofile', '--norc',
            '-c', cmd,
        ])

