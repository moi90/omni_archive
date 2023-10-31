import os
import pathlib
import shutil
from typing import IO, Iterable, Union
from .generic import _ArchivePath, Archive


class DirectoryArchive(Archive):
    """A subclass of Archive for working with filesystem directories."""

    _extensions = [""]

    # Use PurePosixPath PureWindowsPath depending on the system
    _pure_path_impl = pathlib.PurePath

    @staticmethod
    def is_readable(archive_fn: Union[str, pathlib.Path]):
        return pathlib.Path(archive_fn).is_dir()

    def __init__(self, archive_fn: Union[str, pathlib.Path], mode: str = "r"):
        root_path = pathlib.Path(archive_fn)

        if mode == "r" and not root_path.exists():
            raise FileNotFoundError(archive_fn)

        root_path.mkdir(exist_ok=True)

        self._root_path = root_path
        self._mode = mode

    def members(self) -> Iterable[_ArchivePath]:
        for root, dirs, files in os.walk(self._root_path):
            relroot = os.path.relpath(root, self._root_path)
            for fn in files:
                yield _ArchivePath(
                    self, self._pure_path_impl(os.path.join(relroot, fn))
                )

    def open_member(
        self,
        member_fn: Union[str, pathlib.PurePath],
        mode="r",
        *args,
        compress_hint=True,
        **kwargs,
    ) -> IO:
        del compress_hint

        if mode[0] != "r" and self._mode == "r":
            raise ValueError("Archive is read-only")

        return open(self._root_path / member_fn, *args, mode=mode, **kwargs)

    def write_member(
        self,
        member_fn: Union[str, pathlib.PurePath],
        fileobj_or_bytes: Union[IO, bytes],
        *,
        compress_hint=True,
        mode: str = "w",
    ):
        del compress_hint

        with self.open_member(member_fn, mode) as f:
            if hasattr(fileobj_or_bytes, "read"):
                shutil.copyfileobj(fileobj_or_bytes, f)
            else:
                f.write(fileobj_or_bytes)

    def member_is_file(self, member_fn: str | pathlib.PurePath) -> bool:
        return (self._root_path / member_fn).is_file()

    def member_exists(self, member_fn: str | pathlib.PurePath) -> bool:
        return (self._root_path / member_fn).exists()

    def close(self):
        pass
