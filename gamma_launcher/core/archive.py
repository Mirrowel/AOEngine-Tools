import logging
from pathlib import Path
from typing import Optional
import shutil
import tarfile
import zipfile

import py7zr

try:
    import rarfile
except ImportError:  # pragma: no cover - rarfile optional during development
    rarfile = None


class ArchiveExtractor:
    """Extracts various archive formats used by GAMMA."""

    def extract(self, archive_path: Path, destination: Path, member_filter: Optional[str] = None) -> None:
        logging.info(f"Extracting {archive_path} to {destination}")
        destination.mkdir(parents=True, exist_ok=True)

        if archive_path.suffix.lower() == '.7z':
            self._extract_7z(archive_path, destination, member_filter)
        elif archive_path.suffix.lower() in {'.zip', '.jar'}:
            self._extract_zip(archive_path, destination, member_filter)
        elif archive_path.suffix.lower() in {'.tar', '.gz', '.tgz'}:
            self._extract_tar(archive_path, destination)
        elif archive_path.suffix.lower() in {'.rar'} and rarfile:
            self._extract_rar(archive_path, destination)
        else:
            logging.warning(f"Unsupported archive type for {archive_path.name}. Copying instead.")
            self._copy_single_file(archive_path, destination)

    def _extract_7z(self, archive_path: Path, destination: Path, member_filter: Optional[str]) -> None:
        with py7zr.SevenZipFile(archive_path, mode='r') as archive:
            if member_filter:
                allfiles = archive.getnames()
                filtered = [f for f in allfiles if member_filter in f]
                if not filtered:
                    filtered = allfiles
                archive.extract(path=destination, targets=filtered)
            else:
                archive.extractall(path=destination)

    def _extract_zip(self, archive_path: Path, destination: Path, member_filter: Optional[str]) -> None:
        with zipfile.ZipFile(archive_path, 'r') as archive:
            members = archive.namelist()
            if member_filter:
                members = [m for m in members if member_filter in m]
                if not members:
                    members = archive.namelist()
            archive.extractall(path=destination, members=members)

    def _extract_tar(self, archive_path: Path, destination: Path) -> None:
        with tarfile.open(archive_path, 'r:*') as archive:
            archive.extractall(path=destination)

    def _extract_rar(self, archive_path: Path, destination: Path) -> None:
        if rarfile is None:
            raise RuntimeError("rarfile module is required to extract RAR archives.")
        rf = rarfile.RarFile(archive_path)
        rf.extractall(path=destination)

    def _copy_single_file(self, archive_path: Path, destination: Path) -> None:
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy(archive_path, destination / archive_path.name)
