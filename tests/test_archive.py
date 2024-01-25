import io
import pathlib
import tarfile
import zipfile

import pytest

from omni_archive import Archive


@pytest.mark.parametrize("ext", [".zip", ".tar", ""])
@pytest.mark.parametrize("compress_hint", [True, False])
def test_Archive(tmp_path, ext, compress_hint):
    archive_path: pathlib.Path = tmp_path / ("archive" + ext)

    spam_fn: pathlib.Path = tmp_path / "spam.txt"
    spam_fn.touch()

    with Archive(archive_path, "w") as archive:
        with (archive / "foo.txt").open("w") as f:
            f.write("foo")

        archive.write_member("bar.txt", b"bar", compress_hint=compress_hint, mode="wb")

        assert (archive / "bar.txt").is_file()
        assert (archive / "bar.txt").exists()

        archive.write_member("baz.txt", io.BytesIO(b"baz"), mode="wb")

        assert (archive / "baz.txt").is_file()

        with open(spam_fn) as f:
            archive.write_member(spam_fn.name, f, mode="wb")

        assert (archive / spam_fn.name).is_file()

        assert set(str(m) for m in archive.members()) == {
            str(archive_path / "foo.txt"),
            str(archive_path / "bar.txt"),
            str(archive_path / "baz.txt"),
            str(archive_path / "spam.txt"),
        }

        assert set(str(m) for m in archive.glob("b*.txt")) == {
            str(archive_path / "bar.txt"),
            str(archive_path / "baz.txt"),
        }

        assert set(str(m) for m in archive.iterdir()) == set(
            str(m) for m in archive.glob("*")
        )

        dir1 = archive / "dir1"

        with (dir1 / "foo.txt").open("w") as f:
            f.write("foo")

        assert set(str(m) for m in dir1.iterdir()) == set(
            str(m) for m in dir1.glob("*")
        )

    if ext == ".zip":
        assert zipfile.is_zipfile(archive_path), f"{archive_path} is not a zip file"
    elif ext == ".tar":
        assert tarfile.is_tarfile(archive_path), f"{archive_path} is not a tar file"
    elif ext == "":
        assert archive_path.is_dir(), f"{archive_path} is not a directory"

    with Archive(archive_path, "r") as archive:
        with (archive / "foo.txt").open("r") as f:
            contents = f.read()
        assert contents == "foo"
