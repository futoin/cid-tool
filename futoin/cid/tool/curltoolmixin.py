
class CurlToolMixIn(object):
    __slots__ = ()

    def getDeps(self):
        return ['curl']

    def _callCurl(self, env, curl_args, *args, **nargs):
        cmd = [env['curlBin'], '-fsSL']
        cmd += self._configutil.timeouts(env, 'curl')
        cmd += ['-A', 'FutoIn CID']
        cmd += curl_args

        return self._executil.callExternal(
            cmd,
            *args, **nargs
        )
