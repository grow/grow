"""Track the jinja2 rendering dependencies."""

import jinja2

class DepEnvironment(jinja2.Environment):
    """Override to track the dependencies for the current doc."""

    # pylint: disable=redefined-builtin
    def _load_template(self, name, globals):
        if 'g' in globals and '_track_dependency' in globals['g']:
            globals['g']['_track_dependency'](name)
        return super(DepEnvironment, self)._load_template(name, globals)
