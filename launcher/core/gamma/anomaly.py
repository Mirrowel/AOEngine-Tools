"""
Anomaly Base Game Installer

Handles downloading and installing S.T.A.L.K.E.R. Anomaly 1.5.3,
the base game required for GAMMA modpack.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional, Callable

from .moddb import ModDBDownloader, ModDBError
from .archive import ArchiveExtractor, ArchiveError

logger = logging.getLogger(__name__)


class AnomalyError(Exception):
    """Base exception for Anomaly installation."""
    pass


class AnomalyInstaller:
    """
    Handles Anomaly base game installation.

    Downloads S.T.A.L.K.E.R. Anomaly 1.5.3 from ModDB and installs it
    to the specified directory. Provides verification and patching capabilities.

    Attributes:
        downloader: ModDB downloader instance
        extractor: Archive extractor instance
    """

    # Anomaly 1.5.3 ModDB URLs
    ANOMALY_VERSION = "1.5.3"
    ANOMALY_DOWNLOAD_URL = "https://www.moddb.com/downloads/start/277404"
    ANOMALY_INFO_URL = "https://www.moddb.com/mods/stalker-anomaly/downloads/stalker-anomaly-153"

    # Required directories in valid Anomaly installation
    REQUIRED_DIRS = ['bin', 'gamedata', 'appdata', 'tools']

    def __init__(self):
        """Initialize Anomaly installer."""
        self.downloader = ModDBDownloader()
        self.extractor = ArchiveExtractor()

    def verify_installation(self, anomaly_path: Path) -> bool:
        """
        Verify Anomaly installation is complete and valid.

        Checks for presence of required directories and key files.

        Args:
            anomaly_path: Path to Anomaly installation

        Returns:
            True if installation is valid, False otherwise
        """
        if not anomaly_path.exists():
            logger.warning(f"Anomaly path does not exist: {anomaly_path}")
            return False

        # Check required directories
        for dir_name in self.REQUIRED_DIRS:
            dir_path = anomaly_path / dir_name
            if not dir_path.is_dir():
                logger.warning(f"Missing required directory: {dir_name}")
                return False

        # Check for executables
        bin_path = anomaly_path / 'bin'
        executables = ['AnomalyDX9.exe', 'AnomalyDX11.exe', 'AnomalyDX11AVX.exe']

        found_exe = False
        for exe in executables:
            if (bin_path / exe).is_file():
                found_exe = True
                break

        if not found_exe:
            logger.warning("No Anomaly executable found in bin/")
            return False

        # Check for user.ltx
        user_ltx = anomaly_path / 'appdata' / 'user.ltx'
        if not user_ltx.is_file():
            logger.warning("user.ltx not found")
            return False

        logger.info("Anomaly installation verified successfully")
        return True

    def download_anomaly(
        self,
        cache_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        use_cached: bool = True
    ) -> Path:
        """
        Download Anomaly 1.5.3 from ModDB.

        Args:
            cache_path: Directory to cache downloaded file
            progress_callback: Progress callback (bytes_downloaded, total_bytes)
            use_cached: Use cached file if available and valid

        Returns:
            Path to downloaded archive

        Raises:
            AnomalyError: If download fails
        """
        logger.info("Downloading S.T.A.L.K.E.R. Anomaly 1.5.3")

        # Determine output filename
        archive_name = "stalker-anomaly-153.7z"
        output_path = cache_path / archive_name

        try:
            self.downloader.download_mod(
                info_url=self.ANOMALY_INFO_URL,
                download_url=self.ANOMALY_DOWNLOAD_URL,
                output_path=output_path,
                expected_md5=None,  # Will be scraped from page
                progress_callback=progress_callback,
                use_cached=use_cached
            )

            logger.info(f"Anomaly downloaded to: {output_path}")
            return output_path

        except ModDBError as e:
            raise AnomalyError(f"Failed to download Anomaly: {e}")

    def extract_anomaly(
        self,
        archive_path: Path,
        anomaly_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        Extract Anomaly archive to installation directory.

        Args:
            archive_path: Path to Anomaly archive
            anomaly_path: Where to install Anomaly
            progress_callback: Progress callback (files_extracted, total_files)

        Raises:
            AnomalyError: If extraction fails
        """
        logger.info(f"Extracting Anomaly to: {anomaly_path}")

        try:
            # Extract to temporary directory first
            temp_extract = anomaly_path.parent / f"{anomaly_path.name}_temp"

            # Clean up any previous temp extraction
            if temp_extract.exists():
                shutil.rmtree(temp_extract)

            # Extract archive
            self.extractor.extract(archive_path, temp_extract, progress_callback)

            # Find the actual game directory (may be nested)
            game_dir = self._find_game_directory(temp_extract)
            if not game_dir:
                raise AnomalyError("Could not locate game directory in archive")

            # Move to final location
            if anomaly_path.exists():
                logger.warning(f"Removing existing Anomaly installation: {anomaly_path}")
                shutil.rmtree(anomaly_path)

            shutil.move(str(game_dir), str(anomaly_path))

            # Clean up temp directory
            if temp_extract.exists():
                shutil.rmtree(temp_extract)

            logger.info("Anomaly extraction complete")

        except ArchiveError as e:
            raise AnomalyError(f"Failed to extract Anomaly: {e}")
        except Exception as e:
            raise AnomalyError(f"Unexpected error during extraction: {e}")

    def _find_game_directory(self, extract_path: Path) -> Optional[Path]:
        """
        Find the actual game directory within extracted archive.

        Anomaly archives may have nested structure, so we need to find
        the directory that contains bin/, gamedata/, etc.

        Args:
            extract_path: Root extraction directory

        Returns:
            Path to game directory, or None if not found
        """
        # Check if extraction root is the game directory
        if all((extract_path / d).is_dir() for d in self.REQUIRED_DIRS):
            return extract_path

        # Search for nested game directory
        for subdir in extract_path.rglob('*'):
            if subdir.is_dir():
                if all((subdir / d).is_dir() for d in self.REQUIRED_DIRS):
                    return subdir

        return None

    def patch_user_ltx(
        self,
        anomaly_path: Path,
        preserve_existing: bool = False,
        wine_mode: bool = False
    ) -> None:
        """
        Patch user.ltx configuration file.

        Applies necessary configuration changes for GAMMA compatibility,
        including fullscreen/borderless mode for Wine.

        Args:
            anomaly_path: Path to Anomaly installation
            preserve_existing: Keep existing user.ltx if present
            wine_mode: Apply Wine-specific patches (borderless mode)

        Raises:
            AnomalyError: If patching fails
        """
        user_ltx = anomaly_path / 'appdata' / 'user.ltx'

        if not user_ltx.exists():
            logger.warning("user.ltx not found, skipping patch")
            return

        if preserve_existing:
            logger.info("Preserving existing user.ltx")
            return

        logger.info("Patching user.ltx for GAMMA")

        try:
            # Read existing config
            with open(user_ltx, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Apply patches
            if wine_mode:
                # Wine requires borderless mode for stability
                logger.info("Applying Wine-specific patches (borderless mode)")
                content = content.replace(
                    'rs_screenmode fullscreen',
                    'rs_screenmode borderless'
                )

            # Write patched config
            with open(user_ltx, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info("user.ltx patched successfully")

        except Exception as e:
            raise AnomalyError(f"Failed to patch user.ltx: {e}")

    def install(
        self,
        anomaly_path: Path,
        cache_path: Path,
        download_progress: Optional[Callable[[int, int], None]] = None,
        extract_progress: Optional[Callable[[int, int], None]] = None,
        skip_if_valid: bool = True,
        wine_mode: bool = False
    ) -> None:
        """
        Complete Anomaly installation workflow.

        Downloads, extracts, and verifies Anomaly installation.

        Args:
            anomaly_path: Where to install Anomaly
            cache_path: Cache directory for downloads
            download_progress: Download progress callback
            extract_progress: Extraction progress callback
            skip_if_valid: Skip installation if valid Anomaly already exists
            wine_mode: Apply Wine-specific configuration

        Raises:
            AnomalyError: If installation fails
        """
        # Check if already installed
        if skip_if_valid and self.verify_installation(anomaly_path):
            logger.info("Valid Anomaly installation found, skipping")
            return

        # Ensure cache directory exists
        cache_path.mkdir(parents=True, exist_ok=True)

        # Download Anomaly
        archive_path = self.download_anomaly(
            cache_path,
            progress_callback=download_progress,
            use_cached=True
        )

        # Extract Anomaly
        self.extract_anomaly(
            archive_path,
            anomaly_path,
            progress_callback=extract_progress
        )

        # Verify installation
        if not self.verify_installation(anomaly_path):
            raise AnomalyError("Anomaly installation verification failed")

        # Apply patches
        self.patch_user_ltx(anomaly_path, preserve_existing=False, wine_mode=wine_mode)

        logger.info("Anomaly installation complete")
