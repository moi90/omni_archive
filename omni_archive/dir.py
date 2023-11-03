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
        archive_fn = pathlib.Path(archive_fn)

        if mode == "r" and not archive_fn.exists():
            raise FileNotFoundError(archive_fn)

        archive_fn.mkdir(exist_ok=True)

        super().__init__(archive_fn, mode)

    def members(self) -> Iterable[_ArchivePath]:
        for root, dirs, files in os.walk(self.archive_fn):
            relroot = os.path.relpath(root, self.archive_fn)
            for fn in files:
                yield _ArchivePath(
                    self, self._pure_path_impl(os.path.join(relroot, fn))
                )

    def glob(self, pattern: str, **kwargs) -> Iterable[_ArchivePath]:
        for match in self.archive_fn.glob(pattern, **kwargs):
            yield _ArchivePath(
                    self, match.relative_to(self.archive_fn))

    def open_member(
        self,
        member_fn: Union[str, pathlib.PurePath],
        mode="r",
        *args,
        compress_hint=True,
        **kwargs,
    ) -> IO:
        del compress_hint

        if mode[0] != "r" and self.mode == "r":
            raise ValueError("Archive is read-only")
        
        (self.archive_fn / member_fn).parent.mkdir(parents=True, exist_ok=True)

        return open(self.archive_fn / member_fn, mode, *args, **kwargs)

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
        return (self.archive_fn / member_fn).is_file()

    def member_exists(self, member_fn: str | pathlib.PurePath) -> bool:
        return (self.archive_fn / member_fn).exists()

    def close(self):
        pass
