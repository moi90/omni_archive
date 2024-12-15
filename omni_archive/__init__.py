"""
OmniArchive

This Python module provides a generic archive reader and writer for various archive formats,
including ZIP, TAR, and regular filesystem directories.
"""

from .generic import Archive, UnknownArchiveError
from .tar import TarArchive
from .zip import ZipArchive
from .dir import DirectoryArchive

__all__ = ["Archive", "UnknownArchiveError", "TarArchive", "ZipArchive", "DirectoryArchive"]

from . import _version

__version__ = _version.get_versions()["version"]
