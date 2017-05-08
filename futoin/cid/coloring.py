
import sys


class Coloring:
    _color = sys.stdout.isatty()

    @classmethod
    def enable(cls, val):
        cls._color = val

    @classmethod
    def wrap(cls, text, escape):
        if cls._color:
            ESC = chr(0x1B)
            return ESC + escape + str(text) + ESC + '[0m'
        else:
            return text

    @classmethod
    def error(cls, text):
        # bright red on black
        return cls.wrap(text, '[1;31;40m')

    @classmethod
    def warn(cls, text):
        # yellow on black
        return cls.wrap(text, '[33;40m')

    @classmethod
    def info(cls, text):
        # cyan on black
        return cls.wrap(text, '[36;40m')

    @classmethod
    def infoLabel(cls, text):
        # bright cyan on black
        return cls.wrap(text, '[1;36;40m')

    @classmethod
    def label(cls, text):
        # bright
        return cls.wrap(text, '[1m')
