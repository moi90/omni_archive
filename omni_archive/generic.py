import abc
from typing import IO, Callable, List, Mapping, Optional, Type, Union
import pathlib

pathlib.PurePosixPath


class MemberNotFoundError(Exception):
    pass


class UnknownArchiveError(Exception):
    """Raised if no handler is found for the requested archive file."""

    pass


class _ArchivePathInterface(abc.ABC):
    """Common path-like interface."""

    @abc.abstractmethod
    def open(self, mode="r", compress_hint=True) -> IO:
        ...

    @abc.abstractmethod
    def __truediv__(self, key: Union[str, pathlib.PurePath]) -> "_ArchivePath":
        ...


class _ArchivePath(_ArchivePathInterface):
    """Represents a path within an archive."""

    def __init__(self, archive: "Archive", path: pathlib.PurePath) -> None:
        self._archive = archive
        self._path = path

    def open(self, mode="r", compress_hint=True) -> IO:
        return self._archive.open_member(self._path, mode, compress_hint)

    def __truediv__(self, key: Union[str, pathlib.PurePath]):
        return _ArchivePath(self._archive, self._path / key)


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
    def is_readable(archive_fn) -> bool:
        """Static method to determine if a subclass can read a certain archive."""
        raise NotImplementedError()  # pragma: no cover

    def __init__(self, archive_fn: Union[str, pathlib.Path], mode: str = "r"):
        raise NotImplementedError()  # pragma: no cover

    def open(self, mode="r", compress_hint=True) -> IO:
        raise

    def open_member(self, member_fn, mode="r", compress_hint=True) -> IO:
        """
        Open an archive member.

        Raises:
            MemberNotFoundError if mode=="r" and the member was not found.
        """

        raise NotImplementedError()  # pragma: no cover

    def find(self, pattern) -> List[str]:
        return fnmatch.filter(self.members(), pattern)

    def members(self) -> List[str]:
        raise NotImplementedError()  # pragma: no cover

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_, **__):
        self.close()

    def __truediv__(self, key: Union[str, pathlib.PurePath]):
        if isinstance(key, str):
            key = self._pure_path_impl(key)

        return _ArchivePath(self, key)
