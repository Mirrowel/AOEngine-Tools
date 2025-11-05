"""
Archive Extraction Utilities

Handles extraction of various archive formats (ZIP, RAR, 7Z) with platform-aware
strategies and FOMOD directive parsing for custom installation layouts.
"""

import logging
import shutil
import subprocess
import zipfile
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, List
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


class ArchiveFormat(Enum):
    """Supported archive formats."""
    ZIP = "zip"
    RAR = "rar"
    SEVENZIP = "7z"
    UNKNOWN = "unknown"


class ArchiveError(Exception):
    """Base exception for archive operations."""
    pass


class UnsupportedFormatError(ArchiveError):
    """Archive format is not supported."""
    pass


class ExtractionError(ArchiveError):
    """Error during archive extraction."""
    pass


class ArchiveExtractor:
    """
    Handles extraction of various archive formats.

    This class provides platform-aware extraction with support for:
    - ZIP files (native zipfile module)
    - RAR files (unrar library or 7z fallback)
    - 7Z files (py7zr library or 7z binary)
    - FOMOD directive parsing for custom layouts

    Attributes:
        use_native: Prefer native Python libraries over external binaries
    """

    def __init__(self, use_native: bool = True):
        """
        Initialize archive extractor.

        Args:
            use_native: Use native Python libraries when possible (default: True)
        """
        self.use_native = use_native

    def detect_format(self, file_path: Path) -> ArchiveFormat:
        """
        Detect archive format by magic bytes and extension.

        Reads the first few bytes of the file to determine the format,
        falling back to file extension if magic bytes are ambiguous.

        Args:
            file_path: Path to archive file

        Returns:
            Detected archive format

        Raises:
            UnsupportedFormatError: If format cannot be determined
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Archive not found: {file_path}")

        # Read magic bytes
        with open(file_path, 'rb') as f:
            magic = f.read(6)

        # Check magic bytes
        if magic[:2] == b'PK':
            return ArchiveFormat.ZIP
        elif magic[:3] == b'Rar':
            return ArchiveFormat.RAR
        elif magic == b'7z\xbc\xaf\x27\x1c':
            return ArchiveFormat.SEVENZIP

        # Fallback to extension
        ext = file_path.suffix.lower()
        if ext == '.zip':
            return ArchiveFormat.ZIP
        elif ext == '.rar':
            return ArchiveFormat.RAR
        elif ext == '.7z':
            return ArchiveFormat.SEVENZIP

        logger.warning(f"Unknown archive format: {file_path}")
        return ArchiveFormat.UNKNOWN

    def extract_zip(
        self,
        archive_path: Path,
        extract_to: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        Extract ZIP archive using native zipfile module.

        Args:
            archive_path: Path to ZIP file
            extract_to: Destination directory
            progress_callback: Called with (files_extracted, total_files)

        Raises:
            ExtractionError: If extraction fails
        """
        logger.info(f"Extracting ZIP: {archive_path} to {extract_to}")

        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                members = zf.namelist()
                total = len(members)

                extract_to.mkdir(parents=True, exist_ok=True)

                for i, member in enumerate(members):
                    zf.extract(member, extract_to)

                    if progress_callback:
                        progress_callback(i + 1, total)

                logger.info(f"Extracted {total} files from ZIP")

        except zipfile.BadZipFile as e:
            raise ExtractionError(f"Invalid ZIP file: {e}")
        except Exception as e:
            raise ExtractionError(f"ZIP extraction failed: {e}")

    def extract_rar(
        self,
        archive_path: Path,
        extract_to: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        Extract RAR archive using unrar library or 7z fallback.

        Args:
            archive_path: Path to RAR file
            extract_to: Destination directory
            progress_callback: Called with (files_extracted, total_files)

        Raises:
            ExtractionError: If extraction fails
        """
        logger.info(f"Extracting RAR: {archive_path} to {extract_to}")

        # Try native unrar library first
        if self.use_native:
            try:
                import rarfile
                with rarfile.RarFile(archive_path, 'r') as rf:
                    members = rf.namelist()
                    total = len(members)

                    extract_to.mkdir(parents=True, exist_ok=True)

                    for i, member in enumerate(members):
                        rf.extract(member, extract_to)

                        if progress_callback:
                            progress_callback(i + 1, total)

                    logger.info(f"Extracted {total} files from RAR")
                    return

            except ImportError:
                logger.warning("rarfile library not available, falling back to 7z")
            except Exception as e:
                logger.warning(f"rarfile extraction failed: {e}, falling back to 7z")

        # Fallback to 7z binary
        self._extract_with_7z(archive_path, extract_to, progress_callback)

    def extract_7z(
        self,
        archive_path: Path,
        extract_to: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        Extract 7Z archive using py7zr library or 7z binary.

        Args:
            archive_path: Path to 7Z file
            extract_to: Destination directory
            progress_callback: Called with (files_extracted, total_files)

        Raises:
            ExtractionError: If extraction fails
        """
        logger.info(f"Extracting 7Z: {archive_path} to {extract_to}")

        # Try native py7zr library first
        if self.use_native:
            try:
                import py7zr
                with py7zr.SevenZipFile(archive_path, 'r') as szf:
                    extract_to.mkdir(parents=True, exist_ok=True)
                    szf.extractall(extract_to)

                    # Count extracted files for progress
                    total = len(list(extract_to.rglob('*')))
                    if progress_callback:
                        progress_callback(total, total)

                    logger.info(f"Extracted 7Z archive")
                    return

            except ImportError:
                logger.warning("py7zr library not available, falling back to 7z")
            except Exception as e:
                logger.warning(f"py7zr extraction failed: {e}, falling back to 7z")

        # Fallback to 7z binary
        self._extract_with_7z(archive_path, extract_to, progress_callback)

    def _extract_with_7z(
        self,
        archive_path: Path,
        extract_to: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        Extract archive using external 7z binary.

        This is the fallback method for all archive types when native
        Python libraries are not available or fail.

        Args:
            archive_path: Path to archive file
            extract_to: Destination directory
            progress_callback: Called with (files_extracted, total_files)

        Raises:
            ExtractionError: If 7z binary not found or extraction fails
        """
        logger.info(f"Extracting with 7z: {archive_path} to {extract_to}")

        # Find 7z binary
        sevenz = shutil.which('7z') or shutil.which('7za')
        if not sevenz:
            raise ExtractionError("7z binary not found in PATH")

        extract_to.mkdir(parents=True, exist_ok=True)

        # Run 7z extraction
        cmd = [sevenz, 'x', '-y', f'-o{extract_to}', str(archive_path)]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Count extracted files
            total = len(list(extract_to.rglob('*')))
            if progress_callback:
                progress_callback(total, total)

            logger.info(f"7z extraction complete: {total} items")

        except subprocess.CalledProcessError as e:
            raise ExtractionError(f"7z extraction failed: {e.stderr}")

    def extract(
        self,
        archive_path: Path,
        extract_to: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        Extract archive automatically detecting format.

        Main entry point for archive extraction. Detects format and
        delegates to appropriate extraction method.

        Args:
            archive_path: Path to archive file
            extract_to: Destination directory
            progress_callback: Called with (files_extracted, total_files)

        Raises:
            UnsupportedFormatError: If format is not supported
            ExtractionError: If extraction fails
        """
        fmt = self.detect_format(archive_path)

        if fmt == ArchiveFormat.ZIP:
            self.extract_zip(archive_path, extract_to, progress_callback)
        elif fmt == ArchiveFormat.RAR:
            self.extract_rar(archive_path, extract_to, progress_callback)
        elif fmt == ArchiveFormat.SEVENZIP:
            self.extract_7z(archive_path, extract_to, progress_callback)
        else:
            raise UnsupportedFormatError(f"Unsupported archive format: {archive_path}")


class FOMODParser:
    """
    Parses FOMOD (Fallout Mod Manager) installation directives.

    FOMOD files define custom installation layouts for mods, specifying
    which folders should be copied where during installation.
    """

    @staticmethod
    def parse_fomod(fomod_path: Path) -> List[tuple[str, str]]:
        """
        Parse FOMOD ModuleConfig.xml for installation directives.

        Args:
            fomod_path: Path to fomod/ModuleConfig.xml

        Returns:
            List of (source, destination) tuples

        Raises:
            FileNotFoundError: If FOMOD file doesn't exist
            ET.ParseError: If XML parsing fails
        """
        if not fomod_path.exists():
            raise FileNotFoundError(f"FOMOD file not found: {fomod_path}")

        logger.info(f"Parsing FOMOD: {fomod_path}")

        try:
            tree = ET.parse(fomod_path)
            root = tree.getroot()

            directives = []

            # Find all <folder> elements with source and destination
            for folder in root.findall('.//folder'):
                source = folder.get('source', '')
                dest = folder.get('destination', '')

                if source:
                    directives.append((source, dest))

            logger.info(f"Found {len(directives)} FOMOD directives")
            return directives

        except ET.ParseError as e:
            logger.error(f"FOMOD XML parsing failed: {e}")
            return []

    @staticmethod
    def apply_fomod_directives(
        extract_path: Path,
        install_path: Path,
        directives: List[tuple[str, str]]
    ) -> None:
        """
        Apply FOMOD installation directives.

        Copies files from source locations to destination locations
        according to FOMOD specifications.

        Args:
            extract_path: Temporary extraction directory
            install_path: Final installation directory
            directives: List of (source, destination) tuples from FOMOD

        Raises:
            FileNotFoundError: If source directory doesn't exist
        """
        logger.info(f"Applying {len(directives)} FOMOD directives")

        for source, dest in directives:
            source_path = extract_path / source
            dest_path = install_path / dest if dest else install_path

            if not source_path.exists():
                logger.warning(f"FOMOD source not found: {source_path}")
                continue

            dest_path.mkdir(parents=True, exist_ok=True)

            # Copy directory contents
            if source_path.is_dir():
                for item in source_path.rglob('*'):
                    if item.is_file():
                        rel_path = item.relative_to(source_path)
                        target = dest_path / rel_path
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target)
            else:
                shutil.copy2(source_path, dest_path)

        logger.info("FOMOD directives applied")


def detect_mod_structure(extract_path: Path) -> Optional[Path]:
    """
    Detect mod directory structure.

    S.T.A.L.K.E.R. mods can have various structures:
    - Direct gamedata folder
    - Nested in subdirectory
    - Multiple folders (appdata, db, gamedata)

    Args:
        extract_path: Extracted archive directory

    Returns:
        Path to root mod directory, or None if structure is ambiguous
    """
    # Check for direct gamedata folder
    gamedata = extract_path / 'gamedata'
    if gamedata.is_dir():
        return extract_path

    # Check for nested structure (single subdirectory)
    subdirs = [d for d in extract_path.iterdir() if d.is_dir()]
    if len(subdirs) == 1:
        nested_gamedata = subdirs[0] / 'gamedata'
        if nested_gamedata.is_dir():
            return subdirs[0]

    # Check for Anomaly mod folders
    anomaly_folders = {'appdata', 'db', 'gamedata'}
    found_folders = {d.name for d in extract_path.iterdir() if d.is_dir()}

    if anomaly_folders & found_folders:  # At least one match
        return extract_path

    # Ambiguous structure
    logger.warning(f"Ambiguous mod structure: {extract_path}")
    return None
