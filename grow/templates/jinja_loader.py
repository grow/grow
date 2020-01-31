"""Custom jinja loaders."""

import jinja2


class FrontMatterLoader(jinja2.FileSystemLoader):
    """Load templates that have possible front matter and strip it off."""

    SEPARATOR = '---'

    def get_source(self, environment, template):
        source, filename, uptodate = super(FrontMatterLoader, self).get_source(
            environment, template)
        # For jinja rendering strip off the front matter.
        if self.SEPARATOR in source:
            source_lines = source.splitlines(True)
            separator_index = None
            for index, line in enumerate(source_lines):
                if line.strip() == self.SEPARATOR:
                    separator_index = index
                    break
            if separator_index:
                source = u''.join(source_lines[separator_index+1:])
        return source, filename, uptodate
