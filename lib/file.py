"""File interaction libraries."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


def next_nonempty_line(file):
    """Returns the next non-empty line of a file.

    Args:
        file: A file object from which to read lines.
    Returns:
        A string containing the next non-whitespace line of the file or None.
    """
    line = file.readline()
    while line.isspace() or len(line) <= 1:
        if line == '':
            return None
        line = file.readline()
    return line


class File(object):
    def __init__(self, content=None, name=None, location=None):

        self.content = content
        self.name = name
        self.location = location


class Tarball(File):
    def __init__(self, name=None, location=None, compression=None):
        File.__init__(self, None, name, location)

        self.compression = compression

    @property
    def content(self):
        # TODO: A tarball's content property should output the full tarball,
        #       including if it is compressed.
        pass


class Ar(File):
    def __init__(self, content=None, name=None, location=None):
        File.__init__(self, content, name, location)

        pass

    @property
    def content(self):
        # TODO: An archive's content property should output the raw archive.
        pass
