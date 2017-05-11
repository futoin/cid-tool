
from ..runtimetool import RuntimeTool


class phpfpmTool(RuntimeTool):
    """PHP is a popular general-purpose scripting language that is especially suited to web development.

Home: http://php.net/

This tool provides PHP-FPM based website entry point support.
It means any PHP file in project can be executed with all consequences.
"""

    def getDeps(self):
        return ['php']

    def tuneDefaults(self):
        return {
            'minMemory': '1M',
            'connMemory': '8M',
            'debugConnOverhead': '24M',
            'socketType': 'unix',
            'scalable': True,
            'maxInstances': 2,
        }
