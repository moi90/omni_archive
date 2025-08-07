"""
OmniArchive

This Python module provides a generic archive reader and writer for various archive formats,
including ZIP, TAR, and regular filesystem directories.
"""

from ._version import __version__  # noqa: F401
from .dir import DirectoryArchive
from .generic import Archive, UnknownArchiveError
from .tar import TarArchive
from .zip import ZipArchive

__all__ = ["Archive", "UnknownArchiveError", "TarArchive", "ZipArchive", "DirectoryArchive"]

