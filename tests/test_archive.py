import io
import pathlib
import tarfile
import zipfile

import pytest

from omni_archive import Archive, UnknownArchiveError
from omni_archive.tar import TarArchive
from omni_archive.zip import ZipArchive


@pytest.mark.parametrize("ext", [".zip", ".tar", ""])
@pytest.mark.parametrize("compress_hint", [True, False])
@pytest.mark.parametrize("as_str", [True, False])
def test_Archive(tmp_path, ext, compress_hint, as_str):
    archive_path: pathlib.Path = tmp_path / ("archive" + ext)

    # Check that a non-existing archive opened in read-mode fails
    with pytest.raises(UnknownArchiveError):
        Archive(archive_path, "r")

    spam_fn: pathlib.Path = tmp_path / "spam.txt"
    spam_fn.touch()

    with Archive(str(archive_path) if as_str else archive_path, "w") as archive:
        # Check that the archive itself can not be `open`ed
        with pytest.raises(IsADirectoryError):
            archive.open()

        assert archive.exists()
        assert not archive.is_file()
        assert archive.match("*")

        assert str(archive) == str(archive_path)

        assert (archive / "foo.txt").match("*")
        assert (archive / "foo.txt").name == "foo.txt"
        assert (archive / "foo.txt").stem == "foo"
        assert (archive / "foo.txt").suffix == ".txt"

        with (archive / "foo.txt").open("w", compress_hint=compress_hint) as f:
            f.write("foo")

        archive.write_member("bar.txt", b"bar", compress_hint=compress_hint, mode="wb")

        assert (archive / "bar.txt").is_file()
        assert (archive / "bar.txt").exists()
        assert not (archive / "baz.txt").is_dir()

        archive.write_member("baz.txt", io.BytesIO(b"baz"), mode="wb")

        assert (archive / "baz.txt").is_file()
        assert not (archive / "baz.txt").is_dir()

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

        assert dir1.is_dir()

        # Check that the Archive behaves like a filesystem root
        root = pathlib.Path("/")
        assert archive.name == root.name
        assert archive.stem == root.stem
        assert archive.suffix == root.suffix
        assert archive.is_dir()

        assert archive.parent == archive

        # Check that members sort properly
        assert [str(m) for m in sorted(archive.members())] == sorted(
            [str(m) for m in archive.members()]
        )

    # Writable archive is now closed
    if isinstance(archive, ZipArchive):
        assert archive._zipfile.fp is None
    elif isinstance(archive, TarArchive):
        assert archive._tarfile.closed  # type: ignore

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

        # Make sure that we can not write to a read-only archive
        with pytest.raises(ValueError):
            (archive / "ham.txt").open("w")

        # Make sure that we can not read a non-existing file
        with pytest.raises(FileNotFoundError):
            (archive / "non-existing.txt").open("r")

    # Readable archive is now closed
    # Make sure the underlying archive is unloaded
    if isinstance(archive, ZipArchive):
        assert "_zipfile" not in archive.__dict__
    elif isinstance(archive, TarArchive):
        assert "_tarfile" not in archive.__dict__
        assert "_members" not in archive.__dict__

    # Readable archive should transparently open again:
    with archive:
        with (archive / "foo.txt").open("r") as f:
            contents = f.read()
        assert contents == "foo"


@pytest.mark.parametrize("ext", [".zip", ".tar", ""])
def test_Archive_nested(tmp_path, ext):
    archive_path: pathlib.Path = tmp_path / ("archive" + ext)

    # Check that a non-existing archive opened in read-mode fails
    with pytest.raises(UnknownArchiveError):
        Archive(archive_path, "r")

    spam_fn: pathlib.Path = tmp_path / "spam.txt"
    spam_fn.touch()

    with Archive(archive_path, "w") as archive:
        sub_archive_path = archive / "sub_archive"
        with Archive(sub_archive_path, "w") as sub_archive:
            with (sub_archive / "foo.txt").open("w") as f:
                f.write("foo")

        assert sub_archive_path.is_dir()

        with Archive(sub_archive_path, "r") as sub_archive:
            assert [m.name for m in sub_archive.members()] == ["foo.txt"]


@pytest.mark.parametrize("ext", [".zip", ".tar", ""])
def test_Archive_comparison(tmp_path, ext):
    archive0_path: pathlib.Path = tmp_path / ("archive0" + ext)
    archive1_path: pathlib.Path = tmp_path / ("archive1" + ext)

    with Archive(archive0_path, "w") as archive0:
        file0 = archive0 / "file.txt"
        file0.touch()

    with Archive(archive1_path, "w") as archive1:
        file1 = archive1 / "file.txt"
        file1.touch()

    assert file0 < file1
