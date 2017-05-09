
class BashToolMixIn(object):
    def getDeps(self):
        return ['bash']

    def _callBash(self, env, cmd=None, bash_args=[], *args, **nargs):
        if cmd:
            cmd_args = ['-c', cmd]
        else:
            cmd_args = ['-s']

        return self._callExternal(
            [env['bashBin'], '--noprofile', '--norc'] + cmd_args + bash_args,
            *args, **nargs)

    def _callBashInteractive(self, env, cmd, replace=True):
        return self._callInteractive([
            env['bashBin'],
            '--noprofile', '--norc',
            '-c', cmd,
        ], replace=replace)
