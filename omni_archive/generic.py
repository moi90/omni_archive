import fnmatch
import pathlib
from typing import IO, Iterable, List, Optional, Type, Union

import fnmatch2
from pathlib_abc import PathBase


class UnknownArchiveError(Exception):
    """Raised if no handler is found for the requested archive file."""

    pass


class _ArchivePath(PathBase):
    """Represents a path within an archive."""

    def __init__(self, archive: "Archive", path: pathlib.PurePath) -> None:
        self._archive = archive
        self._path = path

    def open(self, mode="r", compress_hint=True, **kwargs) -> IO:
        return self._archive.open_member(
            self._path, mode, compress_hint=compress_hint, **kwargs
        )

    def __truediv__(self, key: Union[str, pathlib.PurePath]):
        return _ArchivePath(self._archive, self._path / key)

    def exists(self):
        return self._archive.member_exists(self._path)

    def is_file(self):
        return self._archive.member_is_file(self._path)

    def is_dir(self):
        return self._archive.member_is_dir(self._path)

    def glob(self, pattern: str, **kwargs) -> Iterable["_ArchivePath"]:
        return self._archive.glob(str(self._path / pattern), **kwargs)

    def iterdir(self) -> Iterable["_ArchivePath"]:
        return self._archive._iterdir_at(self._path)

    def match(self, pattern: str, case_sensitive=None) -> bool:
        matches = fnmatch.fnmatchcase if case_sensitive else fnmatch.fnmatch

        return matches(str(self._path), pattern)

    def mkdir(self, **kwargs):
        return self._archive._mkdir_at(self._path, **kwargs)

    def __str__(self) -> str:
        return str(self._archive.archive_fn / self._path)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<{self.__class__.__name__}({self._path})>"

    @property
    def parent(self) -> "_ArchivePath":
        return _ArchivePath(self._archive, self._path.parent)

    def relative_to(self, other) -> pathlib.PurePath:
        if not isinstance(other, _ArchivePath):
            raise ValueError(f"other must be _ArchivePath, got {other!r}")

        if other._archive is not self._archive:
            raise ValueError(f"other must belong to the same Archive")

        return self._path.relative_to(other._path)

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
        if not isinstance(other, _ArchivePath):  # pragma: no cover
            return NotImplemented

        if self._archive.archive_fn != other._archive.archive_fn:  # pragma: no cover
            return NotImplemented

        return self._path < other._path


class Archive(PathBase):
    """
    A generic archive reader and writer for ZIP, TAR and other archives, offering a familiar pathlib-like API.

    An Archiv instance behaves like a root directory: It has no name and is its own parent.
    """

    _extensions: List[str]
    _pure_path_impl: Type[pathlib.PurePath]

    def __new__(
        cls, archive_fn: Union[str, pathlib.Path], mode: str = "r"
    ) -> "Archive":
        if isinstance(archive_fn, str):
            archive_fn = pathlib.Path(archive_fn)

        if mode[0] == "r":
            for subclass in cls.__subclasses__():
                if subclass.is_readable(archive_fn):
                    return super(Archive, subclass).__new__(subclass)

            raise UnknownArchiveError(f"No handler found to read {archive_fn}")

        if mode[0] in ("a", "w", "x"):
            for subclass in cls.__subclasses__():
                if any(archive_fn.name.endswith(ext) for ext in subclass._extensions):
                    return super(Archive, subclass).__new__(subclass)

            raise UnknownArchiveError(
                f"No handler found to write {archive_fn}"
            )  # pragma: no cover

        raise ValueError(f"Unknown mode: {mode}")  # pragma: no cover

    # Not abstract so that the type checker does not complain if Archive is instanciated.
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

    def match(self, pattern: str, **kwargs) -> bool:
        return self.archive_fn.match(pattern, **kwargs)

    def exists(self):
        return True

    def is_file(self):
        return False

    def is_dir(self):
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

    def member_is_dir(self, member_fn: Union[str, pathlib.PurePath]) -> bool:
        """Check if a member is a directory."""

        # This default implementation checks if the supplied member_fn is the parent
        # of any member contained in the archive.
        # This can be slow but it is guaranteed to work with archives
        # that don't explicitely store directories.

        if isinstance(member_fn, str):
            member_fn = self._pure_path_impl(member_fn)

        for member in self.members():
            if member.parent._path == member_fn:
                return True

        return False

    def glob(self, pattern: str, **kwargs) -> Iterable[_ArchivePath]:
        # We use fnmatch2 here, instead of member.match.
        # With member.match, * would match arbitrarily deep which only ** should do
        # We could also use pywildcard.fnmatch.
        # TODO: Investigate performance differences

        fnmatch2_ = (
            fnmatch2.fnmatchcase2
            if kwargs.get("case_sensitive", False)
            else fnmatch2.fnmatch2
        )

        for member in self.members():
            if fnmatch2_(str(member._path), pattern):
                yield member

    def iterdir(self) -> Iterable["_ArchivePath"]:
        return self._iterdir_at()

    def _iterdir_at(
        self, at: Optional[pathlib.PurePath] = None
    ) -> Iterable[_ArchivePath]:
        if at is None:
            at = self._pure_path_impl(".")

        for member in self.members():
            if member.parent._path == at:
                yield member

    def _mkdir_at(self, at: pathlib.PurePath, **kwargs):
        raise NotImplementedError()  # pragma: no cover

    def close(self):  # pragma: no cover
        """
        Close the archive and free resources.

        For archives in (w/x)-mode, it is an error to access it after closing.
        """
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
    def parent(self):
        return self

    @property
    def name(self) -> str:
        return ""

    @property
    def suffix(self) -> str:
        return ""

    @property
    def stem(self) -> str:
        return ""

    def __lt__(self, other) -> bool:
        if isinstance(other, Archive):
            return self.archive_fn < other.archive_fn

        return NotImplemented  # pragma: no cover

    def __str__(self) -> str:
        return str(self.archive_fn)
