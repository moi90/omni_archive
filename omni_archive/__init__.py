"""..."""

from .generic import Archive
from .tar import TarArchive
from .zip import ZipArchive
from .dir import DirectoryArchive

from . import _version

__version__ = _version.get_versions()["version"]

__all__ = ["Archive"]
