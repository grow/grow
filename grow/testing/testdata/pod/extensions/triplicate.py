"""Example (but pointless) custom Jinja Extension."""
from jinja2.ext import Extension


def triplicate(value):
    return value + value + value


class Triplicate(Extension):
    def __init__(self, environment):
        super(Triplicate, self).__init__(environment)
        environment.filters['triplicate'] = triplicate
