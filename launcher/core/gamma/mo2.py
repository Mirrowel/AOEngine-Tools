"""
ModOrganizer2 Setup and Configuration

Handles downloading, installing, and configuring ModOrganizer2 for GAMMA.
Sets up portable mode, creates profiles, and generates modlist.txt.
"""

import configparser
import logging
import shutil
from pathlib import Path
from typing import Optional, Callable, List

import requests

from .archive import ArchiveExtractor, ArchiveError

logger = logging.getLogger(__name__)


class MO2Error(Exception):
    """Base exception for ModOrganizer2 operations."""
    pass


class MO2Manager:
    """
    Handles ModOrganizer2 setup and configuration.

    Downloads MO2 from GitHub, sets up portable mode, creates profiles,
    and configures for GAMMA installation.

    Attributes:
        extractor: Archive extractor instance
        timeout: Request timeout in seconds
    """

    # GitHub repository for ModOrganizer2
    MO2_REPO_URL = "https://github.com/ModOrganizer2/modorganizer/releases/download"
    MO2_DEFAULT_VERSION = "v2.4.4"

    def __init__(self, timeout: int = 300):
        """
        Initialize MO2 manager.

        Args:
            timeout: Request timeout in seconds
        """
        self.extractor = ArchiveExtractor()
        self.timeout = timeout

    def download_mo2(
        self,
        version: str,
        cache_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        use_cached: bool = True
    ) -> Path:
        """
        Download ModOrganizer2 from GitHub.

        Args:
            version: MO2 version (GitHub tag, e.g., "v2.4.4")
            cache_path: Cache directory
            progress_callback: Progress callback (bytes_downloaded, total_bytes)
            use_cached: Use cached file if available

        Returns:
            Path to downloaded archive

        Raises:
            MO2Error: If download fails
        """
        logger.info(f"Downloading ModOrganizer2 {version}")

        # Construct download URL
        filename = f"Mod.Organizer-{version}.7z"
        download_url = f"{self.MO2_REPO_URL}/{version}/{filename}"
        output_path = cache_path / filename

        # Check cache
        if use_cached and output_path.exists():
            logger.info(f"Using cached MO2: {output_path}")
            return output_path

        # Download
        try:
            cache_path.mkdir(parents=True, exist_ok=True)

            response = requests.get(download_url, stream=True, timeout=self.timeout)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)

            logger.info(f"MO2 downloaded to: {output_path}")
            return output_path

        except requests.RequestException as e:
            if output_path.exists():
                output_path.unlink()
            raise MO2Error(f"Failed to download MO2: {e}")

    def extract_mo2(
        self,
        archive_path: Path,
        mo2_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        Extract MO2 archive to installation directory.

        Args:
            archive_path: Path to MO2 archive
            mo2_path: Where to install MO2
            progress_callback: Progress callback (files_extracted, total_files)

        Raises:
            MO2Error: If extraction fails
        """
        logger.info(f"Extracting MO2 to: {mo2_path}")

        try:
            # Clean up existing installation
            if mo2_path.exists():
                logger.warning(f"Removing existing MO2 installation: {mo2_path}")
                shutil.rmtree(mo2_path)

            mo2_path.mkdir(parents=True, exist_ok=True)

            # Extract archive
            self.extractor.extract(archive_path, mo2_path, progress_callback)

            logger.info("MO2 extraction complete")

        except ArchiveError as e:
            raise MO2Error(f"Failed to extract MO2: {e}")

    def setup_portable_mode(self, mo2_root: Path) -> None:
        """
        Set up MO2 in portable mode.

        Creates portable.txt file that tells MO2 to use local directories
        instead of AppData.

        Args:
            mo2_root: MO2 installation root (parent of ModOrganizer.exe)

        Raises:
            MO2Error: If setup fails
        """
        logger.info("Setting up MO2 portable mode")

        portable_file = mo2_root / 'portable.txt'

        try:
            portable_file.touch(exist_ok=True)
            logger.info("Portable mode enabled")

        except Exception as e:
            raise MO2Error(f"Failed to create portable.txt: {e}")

    def create_profile(
        self,
        mo2_root: Path,
        profile_name: str = "GAMMA"
    ) -> Path:
        """
        Create MO2 profile for GAMMA.

        Args:
            mo2_root: MO2 installation root
            profile_name: Profile name (default: "GAMMA")

        Returns:
            Path to created profile directory

        Raises:
            MO2Error: If profile creation fails
        """
        logger.info(f"Creating MO2 profile: {profile_name}")

        profiles_dir = mo2_root / 'profiles'
        profile_dir = profiles_dir / profile_name

        try:
            profile_dir.mkdir(parents=True, exist_ok=True)

            # Create profile.ini
            profile_ini = profile_dir / 'profile.ini'
            self._write_profile_ini(profile_ini)

            # Create empty modlist.txt (will be populated later)
            modlist_txt = profile_dir / 'modlist.txt'
            modlist_txt.touch(exist_ok=True)

            logger.info(f"Profile created: {profile_dir}")
            return profile_dir

        except Exception as e:
            raise MO2Error(f"Failed to create profile: {e}")

    def _write_profile_ini(self, profile_ini: Path) -> None:
        """
        Write profile.ini configuration file.

        Args:
            profile_ini: Path to profile.ini
        """
        config = configparser.ConfigParser()
        config['General'] = {
            'LocalSaves': 'true',
            'LocalSettings': 'true',
            'AutomaticArchiveInvalidation': 'true'
        }

        with open(profile_ini, 'w') as f:
            config.write(f)

    def generate_modlist(
        self,
        profile_dir: Path,
        mod_names: List[str],
        enabled_pattern: str = "+"
    ) -> None:
        """
        Generate modlist.txt for MO2 profile.

        Creates the modlist.txt file that defines load order and
        which mods are enabled.

        Args:
            profile_dir: Profile directory
            mod_names: List of mod names in load order
            enabled_pattern: Prefix for enabled mods (default: "+")

        Raises:
            MO2Error: If modlist generation fails
        """
        logger.info(f"Generating modlist.txt with {len(mod_names)} mods")

        modlist_txt = profile_dir / 'modlist.txt'

        try:
            with open(modlist_txt, 'w', encoding='utf-8') as f:
                for mod_name in mod_names:
                    # Format: +ModName or -ModName or *ModName (separator)
                    if mod_name.endswith('_separator'):
                        f.write(f"*{mod_name}\n")
                    else:
                        f.write(f"{enabled_pattern}{mod_name}\n")

            logger.info(f"Modlist generated: {modlist_txt}")

        except Exception as e:
            raise MO2Error(f"Failed to generate modlist: {e}")

    def configure_mo2_ini(
        self,
        mo2_root: Path,
        anomaly_path: Path,
        profile_name: str = "GAMMA"
    ) -> None:
        """
        Configure ModOrganizer.ini with Anomaly path and settings.

        Args:
            mo2_root: MO2 installation root
            anomaly_path: Path to Anomaly installation
            profile_name: Active profile name

        Raises:
            MO2Error: If configuration fails
        """
        logger.info("Configuring ModOrganizer.ini")

        mo2_ini = mo2_root / 'ModOrganizer.ini'

        try:
            config = configparser.ConfigParser()

            # If ini exists, read it first
            if mo2_ini.exists():
                config.read(mo2_ini)

            # General settings
            if 'General' not in config:
                config['General'] = {}

            config['General']['gamePath'] = str(anomaly_path.resolve())
            config['General']['gameName'] = 'S.T.A.L.K.E.R. Anomaly'
            config['General']['selected_profile'] = profile_name
            config['General']['language'] = 'en'

            # Settings
            if 'Settings' not in config:
                config['Settings'] = {}

            config['Settings']['check_for_updates'] = 'false'
            config['Settings']['compact_downloads'] = 'true'
            config['Settings']['hide_api_counter'] = 'true'

            # Write configuration
            with open(mo2_ini, 'w') as f:
                config.write(f)

            logger.info("ModOrganizer.ini configured")

        except Exception as e:
            raise MO2Error(f"Failed to configure ModOrganizer.ini: {e}")

    def verify_installation(self, mo2_root: Path) -> bool:
        """
        Verify MO2 installation is complete.

        Args:
            mo2_root: MO2 installation root

        Returns:
            True if installation is valid
        """
        mo2_exe = mo2_root / 'ModOrganizer.exe'
        if not mo2_exe.is_file():
            logger.warning("ModOrganizer.exe not found")
            return False

        # Check for essential DLLs
        required_dlls = ['uibase.dll', 'helper.dll']
        for dll in required_dlls:
            if not (mo2_root / dll).is_file():
                logger.warning(f"Missing required DLL: {dll}")
                return False

        logger.info("MO2 installation verified")
        return True

    def install(
        self,
        mo2_root: Path,
        anomaly_path: Path,
        cache_path: Path,
        version: str = MO2_DEFAULT_VERSION,
        download_progress: Optional[Callable[[int, int], None]] = None,
        extract_progress: Optional[Callable[[int, int], None]] = None,
        skip_if_valid: bool = True
    ) -> None:
        """
        Complete MO2 installation and setup workflow.

        Downloads, extracts, and configures ModOrganizer2 for GAMMA.

        Args:
            mo2_root: Where to install MO2 (usually .Grok's Modpack Installer)
            anomaly_path: Path to Anomaly installation
            cache_path: Cache directory for downloads
            version: MO2 version to install
            download_progress: Download progress callback
            extract_progress: Extraction progress callback
            skip_if_valid: Skip if valid MO2 already installed

        Raises:
            MO2Error: If installation fails
        """
        # Check if already installed
        if skip_if_valid and self.verify_installation(mo2_root):
            logger.info("Valid MO2 installation found, skipping")
            return

        # Ensure cache directory exists
        cache_path.mkdir(parents=True, exist_ok=True)

        # Download MO2
        archive_path = self.download_mo2(
            version,
            cache_path,
            progress_callback=download_progress,
            use_cached=True
        )

        # Extract MO2
        self.extract_mo2(
            archive_path,
            mo2_root,
            progress_callback=extract_progress
        )

        # Verify installation
        if not self.verify_installation(mo2_root):
            raise MO2Error("MO2 installation verification failed")

        # Set up portable mode
        self.setup_portable_mode(mo2_root)

        # Create GAMMA profile
        self.create_profile(mo2_root, "GAMMA")

        # Configure MO2
        self.configure_mo2_ini(mo2_root, anomaly_path, "GAMMA")

        logger.info("MO2 installation complete")
