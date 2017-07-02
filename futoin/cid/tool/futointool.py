
from ..runenvtool import RunEnvTool


class futoinTool(RunEnvTool):
    """futoin.json updater as defined in FTN16.

Home: https://github.com/futoin/specs/blob/master/draft/ftn16_cid_tool.md

futoin.json is the only file read by FutoIn CID itself.
"""
    __slots__ = ()
    _FUTOIN_JSON = 'futoin.json'

    def autoDetectFiles(self):
        return self._FUTOIN_JSON

    def initEnv(self, env):
        self._have_tool = True

    def updateProjectConfig(self, config, updates):
        def updater(json):
            for f in ('name', 'version'):
                if f in updates:
                    json[f] = updates[f]

        return self._pathutil.updateJSONConfig(self._FUTOIN_JSON, updater)
