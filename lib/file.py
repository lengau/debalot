"""Class definitions for types of file."""


class File:
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
