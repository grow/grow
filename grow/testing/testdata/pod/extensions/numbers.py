from babel import numbers
import jinja2.ext


class NumbersExtension(jinja2.ext.Extension):

    def __init__(self, environment):
        super(NumbersExtension, self).__init__(environment)
        environment.filters['format_currency'] = numbers.format_currency
