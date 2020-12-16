"""Custom jinja loaders."""

import os
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
                # Look for the separator, ignoring the first line.
                if line.strip() == self.SEPARATOR and index > 0:
                    separator_index = index
                    break
            if separator_index:
                fill_lines = [os.linesep] * (separator_index + 1)
                source = u''.join(fill_lines + source_lines[separator_index+1:])
        return source, filename, uptodate
