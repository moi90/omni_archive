import os
import pathlib
import shutil
from typing import IO, Iterable, Union
from .generic import _ArchivePath, Archive


class DirectoryArchive(Archive):
    """A subclass of Archive for working with filesystem directories."""

    _extensions = [""]

    @staticmethod
    def is_readable(archive_fn: Union[str, pathlib.Path]):
        if isinstance(archive_fn, str):
            archive_fn = pathlib.Path(archive_fn)
        return archive_fn.is_dir()

    def __init__(self, archive_fn: Union[str, pathlib.Path], mode: str = "r"):
        if isinstance(archive_fn, str):
            archive_fn = pathlib.Path(archive_fn)

        if isinstance(archive_fn, pathlib.PosixPath):
            self._pure_path_impl = pathlib.PurePosixPath
        elif isinstance(archive_fn, pathlib.WindowsPath):
            self._pure_path_impl = pathlib.PureWindowsPath
        elif isinstance(archive_fn, Archive):
            self._pure_path_impl = archive_fn._pure_path_impl
        elif isinstance(archive_fn, _ArchivePath):
            self._pure_path_impl = archive_fn._archive._pure_path_impl
        else:
            raise ValueError(
                f"Can not detect _pure_path_impl, archive_fn has unknown type: {type(archive_fn)}"
            )

        # Validate mode
        if mode not in ["r", "w"]:  # pragma: no cover
            raise ValueError(f"Expected mode to be 'r', 'a' or 'w', got {mode!r}")

        if mode[0] in "awx":
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
            yield _ArchivePath(self, match.relative_to(self.archive_fn))

    def open_member(
        self,
        member_fn: Union[str, pathlib.PurePath],
        mode="r",
        *args,
        compress_hint=True,
        **kwargs,
    ) -> IO:
        del compress_hint

        if "r" not in mode and self.mode == "r":
            raise ValueError("Can not write to a read-only archive")

        if "r" not in self.mode:
            # Only create parent directories if the archive is writeable
            (self.archive_fn / member_fn).parent.mkdir(parents=True, exist_ok=True)

        return (self.archive_fn / member_fn).open(mode, *args, **kwargs)

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

    def member_is_dir(self, member_fn: str | pathlib.PurePath) -> bool:
        return (self.archive_fn / member_fn).is_dir()

    def member_exists(self, member_fn: str | pathlib.PurePath) -> bool:
        return (self.archive_fn / member_fn).exists()

    def close(self):
        pass

    def _mkdir_at(self, at: pathlib.PurePath, **kwargs):
        return (self.archive_fn / at).mkdir(**kwargs)
