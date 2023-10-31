import abc
import fnmatch
from typing import (
    IO,
    Container,
    Iterable,
    List,
    Optional,
    Type,
    Union,
)
import pathlib


class UnknownArchiveError(Exception):
    """Raised if no handler is found for the requested archive file."""

    pass


def _validate_filemode(mode: str, allowed: Optional[Container] = None):
    if allowed is not None:
        if mode not in allowed:
            raise ValueError(f"Mode {mode!r} not allowed ({allowed!r})")

    for c in "rwax":
        ...

    return {c: c in mode for c in "rwxabt+"}


class _ArchivePathInterface(abc.ABC):
    """Common path-like interface."""

    @abc.abstractmethod
    def open(self, mode="r", compress_hint=True) -> IO:
        ...

    @abc.abstractmethod
    def __truediv__(self, key: Union[str, pathlib.PurePath]) -> "_ArchivePath":
        ...

    @abc.abstractmethod
    def exists(self):
        """Return True if the path points to an existing file or directory."""
        ...

    @abc.abstractmethod
    def glob(self, pattern: str, **kwargs) -> Iterable["_ArchivePath"]:
        """Glob the given relative pattern in the directory represented by this path, yielding all matching files"""
        ...

    @abc.abstractmethod
    def match(self, pattern: str, **kwargs) -> bool:
        """Match this path against the provided glob-style pattern. Return True if matching is successful, False otherwise."""
        ...


class _ArchivePath(_ArchivePathInterface):
    """Represents a path within an archive."""

    def __init__(self, archive: "Archive", path: pathlib.PurePath) -> None:
        self._archive = archive
        self._path = path

    def open(self, mode="r", compress_hint=True) -> IO:
        return self._archive.open_member(self._path, mode, compress_hint=compress_hint)

    def __truediv__(self, key: Union[str, pathlib.PurePath]):
        return _ArchivePath(self._archive, self._path / key)

    def exists(self):
        return self._archive.has_member(self._path)

    def glob(self, pattern: str, **kwargs) -> Iterable["_ArchivePath"]:
        return self._archive.glob(str(self._path / pattern), **kwargs)

    def match(self, pattern: str, case_sensitive=None) -> bool:
        matches = fnmatch.fnmatchcase if case_sensitive else fnmatch.fnmatch

        return matches(str(self._path), pattern)

    def __str__(self) -> str:
        """Return the string representation of the path."""
        return str(self._path)


class Archive(_ArchivePathInterface):
    """
    A generic archive reader and writer for ZIP, TAR and other archives.
    """

    _extensions: List[str]
    _pure_path_impl: Type[pathlib.PurePath]

    def __new__(cls, archive_fn: Union[str, pathlib.Path], mode: str = "r"):
        archive_fn = str(archive_fn)

        if mode[0] == "r":
            for subclass in cls.__subclasses__():
                if subclass.is_readable(archive_fn):
                    return super(Archive, subclass).__new__(subclass)

            raise UnknownArchiveError(f"No handler found to read {archive_fn}")

        if mode[0] in ("a", "w", "x"):
            for subclass in cls.__subclasses__():
                if any(archive_fn.endswith(ext) for ext in subclass._extensions):
                    return super(Archive, subclass).__new__(subclass)

            raise UnknownArchiveError(f"No handler found to write {archive_fn}")

    @staticmethod
    def is_readable(archive_fn: Union[str, pathlib.Path]) -> bool:
        """Static method to determine if a subclass can read a certain archive."""
        raise NotImplementedError()  # pragma: no cover

    def __init__(self, archive_fn: Union[str, pathlib.Path], mode: str = "r"):
        raise NotImplementedError()  # pragma: no cover

    def open(self, mode="r", compress_hint=True) -> IO:
        raise IsADirectoryError(self)

    def match(self, pattern: str, *, case_sensitive=None) -> bool:
        return False

    def exists(self):
        return True

    def open_member(
        self,
        member_fn: Union[str, pathlib.PurePath],
        mode="r",
        *args,
        compress_hint=True,
        **kwargs,
    ) -> IO:
        """
        Open an archive member.

        Raises:
            MemberNotFoundError if mode=="r" and the member was not found.
        """

        raise NotImplementedError()  # pragma: no cover

    def write_member(
        self,
        member_fn: Union[str, pathlib.PurePath],
        fileobj_or_bytes: Union[IO, bytes],
        *,
        compress_hint=True,
        mode: str = "w",
    ):
        """Write an archive member."""
        raise NotImplementedError()  # pragma: no cover

    def members(self) -> Iterable[_ArchivePath]:
        raise NotImplementedError()  # pragma: no cover

    def has_member(self, member_fn: Union[str, pathlib.PurePath]) -> bool:
        """Check if a member exists."""
        raise NotImplementedError()  # pragma: no cover

    def glob(self, pattern: str, *, case_sensitive=None) -> Iterable[_ArchivePath]:
        if case_sensitive is None:
            case_sensitive = True

        for member in self.members():
            if member.match(pattern, case_sensitive=case_sensitive):
                yield member

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_, **__):
        self.close()

    def __truediv__(self, key: Union[str, pathlib.PurePath]) -> _ArchivePath:
        if isinstance(key, str):
            key = self._pure_path_impl(key)

        return _ArchivePath(self, key)
