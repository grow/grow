"""Track the jinja2 rendering dependencies using a custom environment.

Trying to track with a custom loader does not work since the templates are cached
by the environment and only triggers the loader the first time the template is used.

By using a modified version of the code generator and environment, the context
is passed through to `_load_template` method which normally does not need the context.
Since the `_load_template` method is called before the template caching and does
not affect the performance of the template cache.

When updating jinja to a new version:

- The `visit_Include` adds `, context` as an argument to the function.
- The `get_template`, `select_template`, `get_or_select_template` pass the `context`
  argument to the `_load_template` method.
- The `_load_template` method can remain unchanged.
"""

from jinja2 import nodes
from jinja2.compiler import supports_yield_from, CodeGenerator
from jinja2.environment import Environment, Template, TemplateNotFound, TemplatesNotFound
from jinja2._compat import string_types


class DepCodeGenerator(CodeGenerator):
    """Custom code generator for dependency tracking."""

    def visit_Include(self, node, frame):
        """Copied from upstream. Added context arg to `func` call."""
        if node.ignore_missing:
            self.writeline('try:')
            self.indent()

        func_name = 'get_or_select_template'
        if isinstance(node.template, nodes.Const):
            if isinstance(node.template.value, string_types):
                func_name = 'get_template'
            elif isinstance(node.template.value, (tuple, list)):
                func_name = 'select_template'
        elif isinstance(node.template, (nodes.Tuple, nodes.List)):
            func_name = 'select_template'

        # print 'Visit Include'
        self.writeline('template = environment.%s(' % func_name, node)
        self.visit(node.template, frame)
        # Changed from upstream.
        self.write(', %r, context=context)' % self.name)
        if node.ignore_missing:
            self.outdent()
            self.writeline('except TemplateNotFound:')
            self.indent()
            self.writeline('pass')
            self.outdent()
            self.writeline('else:')
            self.indent()

        skip_event_yield = False
        if node.with_context:
            loop = self.environment.is_async and 'async for' or 'for'
            self.writeline('%s event in template.root_render_func('
                           'template.new_context(context.get_all(), True, '
                           '%s)):' % (loop, self.dump_local_context(frame)))
        elif self.environment.is_async:
            self.writeline('for event in (await '
                           'template._get_default_module_async())'
                           '._body_stream:')
        else:
            if supports_yield_from:
                self.writeline('yield from template._get_default_module()'
                               '._body_stream')
                skip_event_yield = True
            else:
                self.writeline('for event in template._get_default_module()'
                               '._body_stream:')

        if not skip_event_yield:
            self.indent()
            self.simple_write('event', frame)
            self.outdent()

        if node.ignore_missing:
            self.outdent()


class DepEnvironment(Environment):
    """Custom environment for dependency tracking."""

    code_generator_class = DepCodeGenerator

    def get_template(self, name, parent=None, globals=None, context=None):
        """Copied from upstream. Added context arg passthrough."""
        if isinstance(name, Template):
            return name
        if parent is not None:
            name = self.join_path(name, parent)
        return self._load_template(name, self.make_globals(globals), context=context)

    def select_template(self, names, parent=None, globals=None, context=None):
        """Copied from upstream. Added context arg passthrough."""
        if not names:
            raise TemplatesNotFound(message=u'Tried to select from an empty list '
                                            u'of templates.')
        globals = self.make_globals(globals)
        for name in names:
            if isinstance(name, Template):
                return name
            if parent is not None:
                name = self.join_path(name, parent)
            try:
                return self._load_template(name, globals, context=context)
            except TemplateNotFound:
                pass
        raise TemplatesNotFound(names)

    def get_or_select_template(self, template_name_or_list,
                               parent=None, globals=None, context=None):
        """Copied from upstream. Added context arg passthrough."""
        if isinstance(template_name_or_list, string_types):
            return self.get_template(template_name_or_list, parent, globals, context=context)
        elif isinstance(template_name_or_list, Template):
            return template_name_or_list
        return self.select_template(template_name_or_list, parent, globals, context=context)

    # pylint: disable=redefined-builtin
    def _load_template(self, name, globals, context=None):
        """Custom template loading that tracks template as a dependency."""
        if context and '_track_dependency' in context:
            context['_track_dependency'](name)
        return super(DepEnvironment, self)._load_template(name, globals)
