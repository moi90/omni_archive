import abc
import pathlib
from typing import IO, Iterable, TypeVar, Union

TPurePathLike = TypeVar("TPurePathLike", bound="PurePathLike")

class PurePathLike(abc.ABC):
    @abc.abstractmethod
    def __truediv__(self: TPurePathLike, key: Union[str, pathlib.PurePath]) -> TPurePathLike:
        ...

    @abc.abstractmethod
    def match(self, pattern: str, **kwargs) -> bool:
        """Match this path against the provided glob-style pattern. Return True if matching is successful, False otherwise."""
        ...

    @abc.abstractproperty
    def parent(self: TPurePathLike) -> TPurePathLike:
        """The logical parent of the path."""
        ...

    @abc.abstractproperty
    def name(self) -> str:
        """A string representing the final path component, excluding the drive and root, if any."""
        ...

    @abc.abstractproperty
    def stem(self) -> str:
        """The final path component, without its suffix."""
        ...

    @abc.abstractproperty
    def suffix(self) -> str:
        """The file extension of the final component, if any."""
        ...

    @abc.abstractmethod
    def __lt__(self, other) -> bool:
        """Comparison, for sorting."""
        ...


PurePathLike.register(pathlib.PurePath)


class PathLike(PurePathLike):
    """Common path-like interface."""

    @abc.abstractmethod
    def open(self, mode="r", compress_hint=True) -> IO:
        ...

    @abc.abstractmethod
    def exists(self):
        """Return True if the path points to an existing file or directory."""
        ...

    @abc.abstractmethod
    def is_file(self):
        """Return True if the path points to a regular file (or a symbolic link pointing to a regular file)."""
        ...

    @abc.abstractmethod
    def glob(self, pattern: str, **kwargs) -> Iterable["PathLike"]:
        """Glob the given relative pattern in the directory represented by this path, yielding all matching files"""
        ...

    @abc.abstractmethod
    def iterdir(self) -> Iterable["PathLike"]:
        """Iterate over the files in this directory."""
        ...


PurePathLike.register(pathlib.Path)
