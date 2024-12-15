import functools
import io
import pathlib
import zipfile
from typing import IO, Iterable, Union

from pathlib_abc import PathBase, PurePathBase

from .generic import Archive, _ArchivePath


class ZipArchive(Archive):
    """A subclass of Archive for working with ZIP archives."""

    _extensions = [".zip"]
    _pure_path_impl = pathlib.PurePosixPath

    @staticmethod
    def is_readable(archive_fn: Union[str, pathlib.Path, PathBase]):
        if isinstance(archive_fn, str):
            archive_fn = pathlib.Path(archive_fn)
        return archive_fn.is_file() and zipfile.is_zipfile(archive_fn)  # type: ignore

    @functools.cached_property
    def _zipfile(self):
        return zipfile.ZipFile(self.archive_fn, self.mode)  # type: ignore

    def members(self) -> Iterable[_ArchivePath]:
        return (_ArchivePath(self, self._pure_path_impl(name)) for name in self._zipfile.namelist())

    def open_at(
        self,
        member_fn: Union[str, pathlib.PurePath, PathBase],
        mode="r",
        *args,
        compress_hint=True,
        **kwargs,
    ) -> IO:
        # Force str type
        member_fn = str(member_fn)

        if mode[0] == "w" and not compress_hint:
            # Disable compression
            member = zipfile.ZipInfo(member_fn)
            member.compress_type = zipfile.ZIP_STORED
        else:
            # Let ZipFile.open select compression and compression level
            member = member_fn

        try:
            stream = self._zipfile.open(member, mode[0])  # type: ignore
        except KeyError as exc:
            raise FileNotFoundError(member_fn) from exc

        if "b" in mode:
            if args or kwargs:
                stream.close()
                raise ValueError("encoding args invalid for binary operation")
            return stream

        # Text mode
        kwargs["encoding"] = kwargs.get("encoding", None) or "utf-8"
        return io.TextIOWrapper(stream, *args, **kwargs)

    def write_member(
        self,
        member_fn: str,
        fileobj_or_bytes: Union[IO, str, bytes],
        *,
        compress_hint=True,
        mode: str = "w",
    ):
        del mode

        compress_type = zipfile.ZIP_DEFLATED if compress_hint else zipfile.ZIP_STORED

        # BytesIO
        if isinstance(fileobj_or_bytes, io.BytesIO):
            data = fileobj_or_bytes.getbuffer()
        # Any other file
        elif hasattr(fileobj_or_bytes, "read"):
            data = fileobj_or_bytes.read()  # type: ignore
        else:
            data = fileobj_or_bytes

        return self._zipfile.writestr(member_fn, data, compress_type=compress_type)

    def close(self):
        if "_zipfile" in self.__dict__:
            self._zipfile.close()
            if self.mode in ("ra"):
                # Remove cached ZipFile instance so that it can be transparently reopened
                self.__dict__.pop("_zipfile", None)

    def exists_at(self, member_fn: Union[str, pathlib.PurePath, PathBase]) -> bool:
        # Force str type
        member_fn = str(member_fn)

        return zipfile.Path(self._zipfile, member_fn).exists()

    def is_file_at(self, member_fn: Union[str, pathlib.PurePath, PathBase]) -> bool:
        # Force str type
        member_fn = str(member_fn)

        return zipfile.Path(self._zipfile, member_fn).is_file()

    def is_dir_at(self, member_fn: Union[str, pathlib.PurePath, PathBase]) -> bool:
        """
        Check if a member is a directory, i.e. it exists as a dir or as a parent of a file and is not a file.
        """
        member_fn = str(member_fn)

        if member_fn.endswith("/"):
            if zipfile.Path(self._zipfile, member_fn).exists():
                return True
        else:
            if zipfile.Path(self._zipfile, member_fn).exists():
                return False

            if zipfile.Path(self._zipfile, member_fn + "/").exists():
                return True

        # If the member is not found, use the generic slow method.
        # Also, for backward compatibility, we treat a regular file whose name ends with a slash as a directory.
        return super().is_dir_at(member_fn)

    def mkdir_at(self, member_fn: Union[str, pathlib.PurePath, PathBase], **kwargs):
        # Check, if mkdir is supported
        try:
            mkdir = self._zipfile.mkdir
        except AttributeError:
            # ZipFile.mkdir is only available since Python 3.11
            # (but directories are optional, anyhow)
            return

        # ZipFile.mkdir does not support these parameters
        kwargs.pop("parents", False)
        exist_ok = kwargs.pop("exist_ok", False)

        # Convert to str
        if not isinstance(member_fn, str):
            member_fn = str(member_fn)

        if not member_fn.endswith("/"):
            member_fn += "/"

        # Check if a file exists (without ending slash)
        if zipfile.Path(self._zipfile, (member_fn[:-1])).exists():
            raise FileExistsError(member_fn)

        # Check if a directory exists
        if zipfile.Path(self._zipfile, (member_fn)).exists():
            if exist_ok:
                return
            raise FileExistsError(member_fn)

        mkdir(member_fn, **kwargs)

    def touch_at(self, at: Union[pathlib.PurePath, PurePathBase], **kwargs):
        self.write_member(str(at), b"")
