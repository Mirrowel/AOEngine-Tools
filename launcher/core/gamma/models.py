"""
GAMMA Data Models

Pydantic models for GAMMA configuration, mod records, and installation state.
These models provide validation, serialization, and type safety for all GAMMA operations.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class GammaConfig(BaseModel):
    """
    GAMMA installation configuration.

    This model stores all configuration options for GAMMA installation including
    paths, installation options, and performance tuning parameters.

    Attributes:
        anomaly_path: Path to Anomaly installation directory
        gamma_path: Path to GAMMA modpack directory (.Grok's Modpack Installer)
        cache_path: Path to cache directory for downloaded files
        mo2_version: ModOrganizer2 version to install (GitHub tag)
        preserve_user_ltx: Keep user.ltx during Anomaly patching
        force_git_download: Force re-download of Git repositories
        check_md5: Verify MD5 hashes for downloaded files
        delete_reshade: Remove ReShade DLLs during installation
        parallel_downloads: Number of parallel download threads (1-8)
        parallel_extractions: Number of parallel extraction threads (1-4)
        download_timeout: Timeout for downloads in seconds (60-600)
        installed_version: Currently installed GAMMA version
        last_update_check: ISO timestamp of last update check
    """

    anomaly_path: Optional[Path] = None
    gamma_path: Optional[Path] = None
    cache_path: Optional[Path] = None
    mo2_version: str = "v2.4.4"

    # Installation options
    preserve_user_ltx: bool = False
    force_git_download: bool = True
    check_md5: bool = True
    delete_reshade: bool = True

    # Performance tuning
    parallel_downloads: int = Field(default=4, ge=1, le=8)
    parallel_extractions: int = Field(default=2, ge=1, le=4)
    download_timeout: int = Field(default=300, ge=60, le=600)

    # Version tracking
    installed_version: Optional[str] = None
    last_update_check: Optional[str] = None

    @field_validator('anomaly_path', 'gamma_path', 'cache_path')
    @classmethod
    def validate_path_exists(cls, v: Optional[Path]) -> Optional[Path]:
        """Ensure paths exist by creating them if needed."""
        if v and not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v

    def is_anomaly_installed(self) -> bool:
        """Check if Anomaly is properly installed."""
        if not self.anomaly_path or not self.anomaly_path.exists():
            return False

        # Check for required directories
        required_dirs = ['bin', 'gamedata', 'appdata']
        return all((self.anomaly_path / d).is_dir() for d in required_dirs)

    def is_mo2_installed(self) -> bool:
        """Check if ModOrganizer2 is installed."""
        if not self.gamma_path:
            return False

        mo2_exe = self.gamma_path / '..' / 'ModOrganizer.exe'
        return mo2_exe.exists()


class ModType(str, Enum):
    """
    Type of mod entry in modpack list.

    Values:
        MODDB: Mod downloaded from ModDB
        GITHUB: Mod from GitHub repository
        SEPARATOR: Folder separator in MO2 (no download)
        GAMMA_LARGE_FILE: Large file from GAMMA repository
    """

    MODDB = "moddb"
    GITHUB = "github"
    SEPARATOR = "separator"
    GAMMA_LARGE_FILE = "gamma_large_file"


class ModRecord(BaseModel):
    """
    Base mod record from modpack_maker_list.txt.

    Represents a single line in the GAMMA modpack definition file. Each mod
    has metadata for downloading, installing, and tracking.

    Attributes:
        url: Download URL (ModDB, GitHub, etc.)
        instructions: FOMOD installation instructions (colon-separated paths or "0")
        patch: Archive extension (.zip, .rar, .7z) or empty
        mod_name: Display name with author (format: "Name - Author")
        info_url: ModDB page or repository URL
        archive_name: Expected filename for caching
        md5_hash: File integrity verification hash (MD5)
        mod_type: Type of mod (MODDB, GITHUB, SEPARATOR, etc.)
        enabled: Whether this mod is enabled in modlist.txt
    """

    url: str
    instructions: str
    patch: str
    mod_name: str
    info_url: Optional[str] = None
    archive_name: Optional[str] = None
    md5_hash: Optional[str] = None

    mod_type: ModType
    enabled: bool = True

    @classmethod
    def from_tsv_line(cls, line: str, enabled: bool = True) -> 'ModRecord':
        """
        Parse tab-separated line into ModRecord.

        Args:
            line: Tab-separated line from modpack_maker_list.txt
            enabled: Whether this mod is enabled (from modlist.txt)

        Returns:
            ModRecord instance (or subclass)

        Raises:
            ValueError: If mod type cannot be determined
        """
        parts = line.strip().split('\t')

        # Detect separator (single field only)
        if len(parts) == 1:
            return SeparatorRecord(mod_name=parts[0])

        # Detect mod type from URL
        url = parts[0]
        if "moddb" in url.lower():
            mod_type = ModType.MODDB
        elif "github" in url.lower():
            mod_type = ModType.GITHUB
        elif "gamma_large_files" in url.lower():
            mod_type = ModType.GAMMA_LARGE_FILE
        else:
            raise ValueError(f"Unknown mod type for URL: {url}")

        # Create appropriate subclass
        if mod_type == ModType.SEPARATOR:
            return SeparatorRecord(mod_name=parts[0])
        else:
            return DownloadableModRecord(
                url=parts[0],
                instructions=parts[1] if len(parts) > 1 else "0",
                patch=parts[2] if len(parts) > 2 else "",
                mod_name=parts[3] if len(parts) > 3 else "Unknown",
                info_url=parts[4] if len(parts) > 4 else None,
                archive_name=parts[5] if len(parts) > 5 else None,
                md5_hash=parts[6] if len(parts) > 6 else None,
                mod_type=mod_type,
                enabled=enabled
            )


class SeparatorRecord(BaseModel):
    """
    Folder separator in ModOrganizer2.

    Separators are visual dividers in the MO2 mod list. They don't contain
    any files, just a meta.ini that marks them as separators.

    Attributes:
        mod_name: Name of the separator
        mod_type: Always SEPARATOR
    """

    mod_name: str
    mod_type: ModType = ModType.SEPARATOR

    def generate_meta_ini(self, index: int) -> str:
        """
        Generate meta.ini content for separator.

        Args:
            index: Separator index for naming

        Returns:
            meta.ini file content
        """
        return f"""[General]
gameName=stalkeranomaly
modid=0
version=
newestVersion=
category=-1
installationFile=
repository=
"""


class DownloadableModRecord(ModRecord):
    """
    Mod that requires download and installation.

    Extends ModRecord with download tracking, progress reporting, and
    meta.ini generation for ModOrganizer2 integration.

    Attributes:
        download_size: File size in bytes (if known)
        download_progress: Download progress (0.0 to 1.0)
        extraction_progress: Extraction progress (0.0 to 1.0)
        installed: Whether mod has been successfully installed
    """

    download_size: Optional[int] = None
    download_progress: float = 0.0
    extraction_progress: float = 0.0
    installed: bool = False

    def get_cache_path(self, cache_dir: Path) -> Path:
        """
        Get cached file path for this mod.

        Args:
            cache_dir: Cache directory root

        Returns:
            Full path to cached file
        """
        filename = self.archive_name or self.url.split('/')[-1]
        return cache_dir / filename

    def generate_meta_ini(self, mod_dir: Path) -> str:
        """
        Generate meta.ini for ModOrganizer.

        Creates a meta.ini file that tells ModOrganizer about this mod's
        metadata, including URL, version, and installation info.

        Args:
            mod_dir: Directory where mod is installed

        Returns:
            meta.ini file content
        """
        return f"""[General]
gameName=stalkeranomaly
modid=0
ignoredversion={self.mod_name}
version={self.mod_name}
installationFile={self.mod_name}
url={self.info_url or self.url}
hasCustomURL=true
color=@Variant(\\0\\0\\0\\x43\\0\\xff\\xff\\0\\0\\0\\0\\0\\0\\0\\0)
tracked=0

[installedFiles]
1\\modid=0
1\\fileid=0
size=1
"""


class InstallationPhase(str, Enum):
    """
    GAMMA installation phase.

    Tracks the current phase of installation to provide accurate progress
    feedback and enable resumption after interruption.

    Values:
        NOT_STARTED: Installation not yet started
        CHECKING_REQUIREMENTS: Verifying disk space, permissions, etc.
        DOWNLOADING_ANOMALY: Downloading base Anomaly 1.5.3
        EXTRACTING_ANOMALY: Extracting Anomaly archive
        DOWNLOADING_MO2: Downloading ModOrganizer2
        DOWNLOADING_GAMMA_DEFINITIONS: Cloning GAMMA Git repositories
        DOWNLOADING_MODS: Downloading individual mods
        EXTRACTING_MODS: Extracting mod archives
        PATCHING_ANOMALY: Applying GAMMA patches to Anomaly
        CONFIGURING_MO2: Setting up MO2 profile and modlist
        FINALIZING: Creating shortcuts, writing version files
        COMPLETED: Installation finished successfully
        FAILED: Installation failed
        CANCELLED: User cancelled installation
    """

    NOT_STARTED = "not_started"
    CHECKING_REQUIREMENTS = "checking_requirements"
    DOWNLOADING_ANOMALY = "downloading_anomaly"
    EXTRACTING_ANOMALY = "extracting_anomaly"
    DOWNLOADING_MO2 = "downloading_mo2"
    DOWNLOADING_GAMMA_DEFINITIONS = "downloading_gamma_definitions"
    DOWNLOADING_MODS = "downloading_mods"
    EXTRACTING_MODS = "extracting_mods"
    PATCHING_ANOMALY = "patching_anomaly"
    CONFIGURING_MO2 = "configuring_mo2"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InstallationState(BaseModel):
    """
    Tracks installation progress and state.

    This model maintains all state information for a GAMMA installation,
    including current phase, progress percentages, file tracking, timing,
    and error/warning collection.

    Attributes:
        phase: Current installation phase
        phase_progress: Progress within current phase (0.0-1.0)
        overall_progress: Overall installation progress (0.0-1.0)
        current_operation: Human-readable description of current operation
        current_file: Name of file currently being processed
        current_file_size: Size of current file in bytes
        current_file_progress: Progress of current file (0.0-1.0)
        total_mods: Total number of mods to install
        downloaded_mods: Number of mods downloaded
        installed_mods: Number of mods installed
        failed_mods: List of mod names that failed to install
        start_time: Installation start timestamp
        end_time: Installation end timestamp
        errors: List of error messages
        warnings: List of warning messages
    """

    phase: InstallationPhase = InstallationPhase.NOT_STARTED
    phase_progress: float = 0.0  # 0.0 to 1.0
    overall_progress: float = 0.0  # 0.0 to 1.0

    current_operation: str = ""
    current_file: Optional[str] = None
    current_file_size: Optional[int] = None
    current_file_progress: float = 0.0

    total_mods: int = 0
    downloaded_mods: int = 0
    installed_mods: int = 0
    failed_mods: List[str] = []

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    errors: List[str] = []
    warnings: List[str] = []

    def get_elapsed_time(self) -> Optional[float]:
        """
        Get elapsed time in seconds.

        Returns:
            Elapsed time in seconds, or None if not started
        """
        if not self.start_time:
            return None
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    def get_estimated_time_remaining(self) -> Optional[float]:
        """
        Estimate remaining time based on progress.

        Uses linear extrapolation based on elapsed time and overall progress.

        Returns:
            Estimated remaining time in seconds, or None if cannot estimate
        """
        elapsed = self.get_elapsed_time()
        if not elapsed or self.overall_progress == 0:
            return None
        return elapsed * (1 - self.overall_progress) / self.overall_progress

    def format_time(self, seconds: Optional[float]) -> str:
        """
        Format time duration as human-readable string.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string (e.g., "5m 30s")
        """
        if seconds is None:
            return "Unknown"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
