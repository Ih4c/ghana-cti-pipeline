"""Private offline workspace, cooperative process locking and bounded disk usage."""

import fcntl
import os
import shutil
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from ghana_cti_pipeline.storage.records import StoreError

LIVE_CAP = 2 * 1024**3
MARGIN = 1024**2
DIRECTORIES = {"backups", "restores", "staging"}
ROOT_FILES = {"live.sqlite", "rights.sqlite", ".lock"}
SUFFIXES = ("-journal", "-wal", "-shm")


def private_file(path: Path):
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    os.close(descriptor)


def fsync_file(path: Path):
    with path.open("rb") as stream:
        os.fsync(stream.fileno())


def fsync_directory(path: Path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def checked(path: Path, *, directory=False):
    info = path.lstat()
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if (
        not expected(info.st_mode)
        or info.st_mode & 0o077
        or info.st_uid != os.geteuid()
        or (not directory and info.st_nlink != 1)
    ):
        raise StoreError("unsafe_workspace")
    return info


@dataclass(frozen=True)
class CapacityReport:
    used_bytes: int
    cap_bytes: int
    free_bytes: int
    warning: bool


class Workspace:
    def __init__(self, root: Path, cap_bytes=LIVE_CAP):
        if type(cap_bytes) is not int or not MARGIN <= cap_bytes <= LIVE_CAP:
            raise StoreError("invalid_capacity_limit")
        self.root = Path(root).absolute()
        self.cap_bytes = cap_bytes
        self.root.mkdir(mode=0o700, exist_ok=True)
        checked(self.root, directory=True)
        lock = self.root / ".lock"
        if not lock.exists():
            try:
                private_file(lock)
            except FileExistsError:
                pass
        checked(lock)

    @contextmanager
    def locked(self):
        lock = self.root / ".lock"
        checked(lock)
        descriptor = os.open(lock, os.O_RDWR | os.O_NOFOLLOW)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise StoreError("workspace_busy") from None
            self.inventory()
            yield
        finally:
            os.close(descriptor)

    def inventory(self):
        files = []
        for child in self.root.iterdir():
            if child.name in DIRECTORIES:
                checked(child, directory=True)
                for entry in child.iterdir():
                    name = entry.name
                    for suffix in SUFFIXES:
                        if name.endswith(suffix):
                            name = name.removesuffix(suffix)
                            break
                    try:
                        valid = name == f"{UUID(name.removesuffix('.sqlite'))}.sqlite"
                    except ValueError:
                        valid = False
                    if not valid:
                        raise StoreError("unexpected_workspace_file")
                    checked(entry)
                    files.append(entry)
            else:
                if child.name not in ROOT_FILES and not any(
                    child.name == base + suffix
                    for base in ("live.sqlite", "rights.sqlite")
                    for suffix in SUFFIXES
                ):
                    raise StoreError("unexpected_workspace_file")
                checked(child)
                files.append(child)
        return files

    def report(self):
        used = sum(checked(path).st_size for path in self.inventory())
        return CapacityReport(
            used,
            self.cap_bytes,
            shutil.disk_usage(self.root).free,
            used * 5 >= self.cap_bytes * 4,
        )

    def reserve(self, extra=0):
        if type(extra) is not int or extra < 0:
            raise StoreError("invalid_reservation")
        report = self.report()
        # Reserve full existing live/ledger rollback journals and a bounded margin.
        journals = sum(
            path.stat().st_size
            for path in (self.root / "live.sqlite", self.root / "rights.sqlite")
            if path.exists()
        )
        needed = journals + extra + MARGIN
        if report.used_bytes + needed > self.cap_bytes or needed > report.free_bytes:
            raise StoreError("capacity_pause")
        return report

    def constrain(self, db, path):
        report = self.report()
        size = path.stat().st_size
        ledger = self.root / "rights.sqlite"
        ledger_size = ledger.stat().st_size if ledger.exists() and path != ledger else 0
        # DB + its worst-case journal have at most half of the remaining allowance each.
        allowance = (self.cap_bytes - (report.used_bytes - size) - ledger_size - MARGIN) // 2
        page_size = db.execute("PRAGMA page_size").fetchone()[0]
        pages = allowance // page_size
        if pages < db.execute("PRAGMA page_count").fetchone()[0] or pages < 1:
            raise StoreError("capacity_pause")
        actual = db.execute(f"PRAGMA max_page_count={pages}").fetchone()[0]
        if actual > pages:
            raise StoreError("capacity_pause")
