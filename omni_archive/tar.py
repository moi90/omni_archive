from .generic import Archive
import tarfile


class _TarIO(io.BytesIO):
    """An auxiliary class to handle TAR archive writing."""

    def __init__(self, archive: "TarArchive", member_fn) -> None:
        super().__init__()
        self.archive = archive
        self.member_fn = member_fn

    def close(self) -> None:
        self.seek(0)
        self.archive.write_member(self.member_fn, self)
        super().close()


class TarArchive(Archive):
    """A subclass of Archive for working with TAR archives."""

    extensions = [
        ".tar",
        ".tar.bz2",
        ".tb2",
        ".tbz",
        ".tbz2",
        ".tz2",
        ".tar.gz",
        ".taz",
        ".tgz",
        ".tar.lzma",
        ".tlz",
    ]

    @staticmethod
    def is_readable(archive_fn):
        return tarfile.is_tarfile(archive_fn)

    def __init__(self, archive_fn: Union[str, pathlib.Path], mode: str = "r"):
        self._tar = tarfile.open(archive_fn, mode)
        self.__members = None

    def close(self):
        self._tar.close()

    def open(self, member_fn, mode="r", compress_hint=True) -> IO:
        # tar does not compress files individually
        del compress_hint

        if mode == "r":
            try:
                fp = self._tar.extractfile(self._resolve_member(member_fn))
            except KeyError as exc:
                raise MemberNotFoundError(
                    f"{member_fn} not in {self._tar.name}"
                ) from exc

            if fp is None:
                raise IOError("There's no data associated with this member")

            return fp

        if mode == "w":
            return _TarIO(self, member_fn)

        raise ValueError(f"Unrecognized mode: {mode}")

    @property
    def _members(self):
        if self.__members is not None:
            return self.__members
        self.__members = {
            tar_info.name: tar_info for tar_info in self._tar.getmembers()
        }
        return self.__members

    def _resolve_member(self, member):
        return self._members[member]

    def write_member(
        self, member_fn: str, fileobj_or_bytes: Union[IO, bytes], compress_hint=True
    ):
        # tar does not compress files individually
        del compress_hint

        if isinstance(fileobj_or_bytes, bytes):
            fileobj_or_bytes = io.BytesIO(fileobj_or_bytes)

        if isinstance(fileobj_or_bytes, io.BytesIO):
            tar_info = tarfile.TarInfo(member_fn)
            tar_info.size = len(fileobj_or_bytes.getbuffer())
        else:
            tar_info = self._tar.gettarinfo(arcname=member_fn, fileobj=fileobj_or_bytes)

        self._tar.addfile(tar_info, fileobj=fileobj_or_bytes)
        self._members[tar_info.name] = tar_info

    def members(self):
        return self._tar.getnames()
