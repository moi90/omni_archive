from .generic import Archive


class DirectoryArchive(Archive):
    """A subclass of Archive for working with filesystem directories."""

    extensions = [""]

    @staticmethod
    def is_readable(archive_fn):
        return os.path.isdir(archive_fn)

    def __init__(self, archive_fn: Union[str, pathlib.Path], mode: str = "r"):
        self.archive_fn = archive_fn
        self.mode = mode

    def members(self):
        def findall():
            for root, dirs, files in os.walk(self.archive_fn):
                relroot = os.path.relpath(root, self.archive_fn)
                for fn in files:
                    yield os.path.join(relroot, fn)

        return list(findall())

    def open(self, member_fn: str, mode="r", compress_hint=True) -> IO:
        return open(os.path.join(self.archive_fn, member_fn), mode=mode)

    def write_member(
        self, member_fn: str, fileobj_or_bytes: Union[IO, bytes], compress_hint=True
    ):
        with self.open(member_fn, "w") as f:
            if isinstance(fileobj_or_bytes, bytes):
                f.write(fileobj_or_bytes)
            else:
                shutil.copyfileobj(fileobj_or_bytes, f)

    def close(self):
        pass
