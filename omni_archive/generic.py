import fnmatch
from typing import (
    IO,
    Iterable,
    List,
    Optional,
    Type,
    Union,
)
import pathlib

from .abc import PathLike, PurePathLike


class UnknownArchiveError(Exception):
    """Raised if no handler is found for the requested archive file."""

    pass


class _ArchivePath(PathLike):
    """Represents a path within an archive."""

    def __init__(self, archive: "Archive", path: pathlib.PurePath) -> None:
        self._archive = archive
        self._path = path

    def open(self, mode="r", compress_hint=True) -> IO:
        return self._archive.open_member(self._path, mode, compress_hint=compress_hint)

    def __truediv__(self, key: Union[str, pathlib.PurePath]):
        return _ArchivePath(self._archive, self._path / key)

    def exists(self):
        return self._archive.member_exists(self._path)

    def is_file(self):
        return self._archive.member_is_file(self._path)

    def glob(self, pattern: str, **kwargs) -> Iterable["_ArchivePath"]:
        return self._archive.glob(str(self._path / pattern), **kwargs)
    
    def iterdir(self) -> Iterable["_ArchivePath"]:
        return self._archive._iterdir_at(self._path)

    def match(self, pattern: str, case_sensitive=None) -> bool:
        matches = fnmatch.fnmatchcase if case_sensitive else fnmatch.fnmatch

        return matches(str(self._path), pattern)

    def __str__(self) -> str:
        """Return the string representation of the path."""
        return str(self._path)
    
    @property
    def parent(self) -> "_ArchivePath":
        return _ArchivePath(self._archive, self._path.parent)

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def stem(self) -> str:
        return self._path.stem

    @property
    def suffix(self) -> str:
        return self._path.suffix

    def __lt__(self, other) -> bool:
        if not isinstance(other, _ArchivePath):
            return NotImplemented

        return self._path < other._path


class Archive(PathLike):
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
        if isinstance(archive_fn, str):
            archive_fn = pathlib.Path(archive_fn)

        self.archive_fn = archive_fn
        self.mode = mode

    def open(self, mode="r", compress_hint=True) -> IO:
        raise IsADirectoryError(self)

    def match(self, pattern: str, *, case_sensitive=None) -> bool:
        return False

    def exists(self):
        return True

    def is_file(self):
        return False

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

        If mode=="w", paths to the requested member are automatically created.

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

    def member_exists(self, member_fn: Union[str, pathlib.PurePath]) -> bool:
        """Check if a member exists."""
        raise NotImplementedError()  # pragma: no cover

    def member_is_file(self, member_fn: Union[str, pathlib.PurePath]) -> bool:
        """Check if a member is a regular file."""
        raise NotImplementedError()  # pragma: no cover

    def glob(self, pattern: str, **kwargs) -> Iterable[_ArchivePath]:
        for member in self.members():
            if member.match(pattern, **kwargs):
                yield member

    def iterdir(self) -> Iterable["_ArchivePath"]:
        return self._iterdir_at()

    def _iterdir_at(self, at: Optional[pathlib.PurePath]=None) -> Iterable[_ArchivePath]:
        if at is None:
            at = self._pure_path_impl(".")

        for member in self.members():
            if member.parent._path == at:
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
    
    @property
    def parent(self) -> _ArchivePath:
        return self / "."

    @property
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def suffix(self) -> str:
        raise NotImplementedError()

    @property
    def stem(self) -> str:
        raise NotImplementedError()

    def __lt__(self, other) -> bool:
        return NotImplemented

    def __str__(self) -> str:
        return str(self.archive_fn)
