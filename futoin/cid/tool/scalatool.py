
from ..runtimetool import RuntimeTool
from .sdkmantoolmixin import SdkmanToolMixIn


class scalaTool(SdkmanToolMixIn, RuntimeTool):
    """The Scala Programming Language.

Home: https://www.scala-lang.org/

Installed via SDKMan!

Requires Java >= 8.
"""
    __slots__ = ()

    def _minJava(self):
        return '8'

    def tuneDefaults(self):
        return {
            'minMemory': '256M',
            'debugOverhead': '128M',
            'connMemory': '100K',
            'debugConnOverhead': '1M',
            'socketType': 'tcp',
            'scalable': False,
        }
