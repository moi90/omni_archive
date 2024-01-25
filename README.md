# OmniArchive

This Python module provides a generic archive reader and writer for various archive formats, including ZIP, TAR, and regular filesystem directories.
It offers a consistent interface following [`pathlib.Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path) for working with these archive types.
The module is designed to be extensible, allowing developers to add support for additional archive formats.

## Alternatives
- [https://pypi.org/project/archive-path/](archive-path) provides a common path interface for different archive types but does not allow nested archives or folder archives.
- [https://pypi.org/project/python-archive/](python-archive) / [https://pypi.org/project/Archive/](archive) provides a common interface for different archive types but no path interface.
- [https://github.com/fake-name/UniversalArchiveInterface](UniversalArchiveInterface) also provides a common interface for different archive types but no path interface.
