"""..."""

from .generic import Archive, UnknownArchiveError
from .tar import TarArchive
from .zip import ZipArchive
from .dir import DirectoryArchive

__all__ = ["Archive"]

from . import _version

__version__ = _version.get_versions()["version"]
