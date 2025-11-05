"""
GAMMA Installer Orchestrator

Main orchestrator for complete GAMMA installation workflow.
Coordinates all installation phases from Anomaly base to final configuration.
"""

import logging
import platform
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
import subprocess

from .models import GammaConfig, InstallationPhase, InstallationState
from .anomaly import AnomalyInstaller, AnomalyError
from .mo2 import MO2Manager, MO2Error
from .mod_manager import ModManager, ModManagerError

logger = logging.getLogger(__name__)


class GammaInstallerError(Exception):
    """Base exception for GAMMA installer."""
    pass


class GammaInstaller:
    """
    Orchestrates complete GAMMA installation.

    This is the main entry point for GAMMA installation. It coordinates
    all phases from requirements checking through final configuration.

    Phases:
        1. Check requirements (disk space, permissions)
        2. Download and install Anomaly 1.5.3
        3. Download and install ModOrganizer2
        4. Download GAMMA definitions (Git repositories)
        5. Download mods in parallel
        6. Install mods in parallel
        7. Patch Anomaly configuration
        8. Configure MO2 profile and modlist
        9. Finalize (create shortcuts, write version files)

    Attributes:
        config: GAMMA configuration
        state: Installation state tracker
        anomaly_installer: Anomaly installer instance
        mo2_manager: MO2 manager instance
        mod_manager: Mod manager instance
    """

    # GAMMA Git repositories
    GAMMA_REPO_URL = "https://github.com/Grokitach/Stalker_GAMMA.git"
    GAMMA_LARGE_FILES_URL = "https://github.com/Grokitach/gamma_large_files_v2.git"

    def __init__(
        self,
        config: GammaConfig,
        state_callback: Optional[Callable[[InstallationState], None]] = None
    ):
        """
        Initialize GAMMA installer.

        Args:
            config: GAMMA configuration
            state_callback: Called whenever installation state changes
        """
        self.config = config
        self.state = InstallationState()
        self.state_callback = state_callback

        # Initialize component installers
        self.anomaly_installer = AnomalyInstaller()
        self.mo2_manager = MO2Manager()
        self.mod_manager = ModManager(
            max_parallel_downloads=config.parallel_downloads,
            max_parallel_extractions=config.parallel_extractions
        )

    def _update_state(
        self,
        phase: Optional[InstallationPhase] = None,
        operation: Optional[str] = None,
        phase_progress: Optional[float] = None,
        overall_progress: Optional[float] = None
    ) -> None:
        """
        Update installation state and notify callback.

        Args:
            phase: New installation phase
            operation: Current operation description
            phase_progress: Progress within current phase (0.0-1.0)
            overall_progress: Overall installation progress (0.0-1.0)
        """
        if phase is not None:
            self.state.phase = phase

        if operation is not None:
            self.state.current_operation = operation

        if phase_progress is not None:
            self.state.phase_progress = phase_progress

        if overall_progress is not None:
            self.state.overall_progress = overall_progress

        if self.state_callback:
            self.state_callback(self.state)

    def _add_error(self, message: str) -> None:
        """Add error message to state."""
        logger.error(message)
        self.state.errors.append(message)
        if self.state_callback:
            self.state_callback(self.state)

    def _add_warning(self, message: str) -> None:
        """Add warning message to state."""
        logger.warning(message)
        self.state.warnings.append(message)
        if self.state_callback:
            self.state_callback(self.state)

    def detect_wine(self) -> bool:
        """
        Detect if running under Wine.

        Returns:
            True if Wine environment detected
        """
        # Check for Wine-specific environment variables
        wine_vars = ['WINE', 'WINEPREFIX', 'WINEDLLPATH', 'WINELOADER']
        for var in wine_vars:
            if var in os.environ:
                return True

        # Check platform
        if platform.system() != 'Windows':
            return True

        return False

    def check_requirements(self) -> bool:
        """
        Check system requirements for GAMMA installation.

        Verifies:
        - Disk space (>100GB free)
        - Paths are writable
        - Git is installed

        Returns:
            True if requirements met, False otherwise
        """
        self._update_state(
            phase=InstallationPhase.CHECKING_REQUIREMENTS,
            operation="Checking system requirements...",
            overall_progress=0.0
        )

        logger.info("Checking system requirements")

        # Check disk space
        if self.config.anomaly_path:
            try:
                stat = shutil.disk_usage(self.config.anomaly_path.parent)
                free_gb = stat.free / (1024**3)

                if free_gb < 100:
                    self._add_error(
                        f"Insufficient disk space: {free_gb:.1f}GB free, need >100GB"
                    )
                    return False

                logger.info(f"Disk space OK: {free_gb:.1f}GB free")

            except Exception as e:
                self._add_warning(f"Could not check disk space: {e}")

        # Check paths are writable
        for path_name, path in [
            ('anomaly_path', self.config.anomaly_path),
            ('gamma_path', self.config.gamma_path),
            ('cache_path', self.config.cache_path)
        ]:
            if path:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    test_file = path / '.write_test'
                    test_file.touch()
                    test_file.unlink()
                    logger.info(f"{path_name} is writable: {path}")

                except Exception as e:
                    self._add_error(f"{path_name} is not writable: {e}")
                    return False

        # Check Git is installed
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Git OK: {result.stdout.strip()}")

        except (subprocess.CalledProcessError, FileNotFoundError):
            self._add_error("Git is not installed or not in PATH")
            return False

        logger.info("Requirements check passed")
        return True

    def clone_gamma_repos(self) -> bool:
        """
        Clone GAMMA Git repositories.

        Clones:
        - Stalker_GAMMA (main modpack definitions)
        - gamma_large_files_v2 (large binary files)

        Returns:
            True if successful
        """
        self._update_state(
            phase=InstallationPhase.DOWNLOADING_GAMMA_DEFINITIONS,
            operation="Cloning GAMMA repositories...",
            overall_progress=0.2
        )

        logger.info("Cloning GAMMA repositories")

        if not self.config.gamma_path:
            self._add_error("GAMMA path not configured")
            return False

        repos = [
            ("Stalker_GAMMA", self.GAMMA_REPO_URL),
            ("gamma_large_files_v2", self.GAMMA_LARGE_FILES_URL)
        ]

        for repo_name, repo_url in repos:
            repo_path = self.config.gamma_path / repo_name

            try:
                if repo_path.exists() and (repo_path / '.git').is_dir():
                    # Repository exists, pull latest
                    logger.info(f"Updating {repo_name}")
                    self._update_state(operation=f"Updating {repo_name}...")

                    subprocess.run(
                        ['git', '-C', str(repo_path), 'pull'],
                        check=True,
                        capture_output=True
                    )

                else:
                    # Clone repository
                    logger.info(f"Cloning {repo_name}")
                    self._update_state(operation=f"Cloning {repo_name}...")

                    subprocess.run(
                        ['git', 'clone', repo_url, str(repo_path)],
                        check=True,
                        capture_output=True
                    )

                logger.info(f"{repo_name} ready")

            except subprocess.CalledProcessError as e:
                self._add_error(f"Failed to clone {repo_name}: {e.stderr}")
                return False

        logger.info("GAMMA repositories cloned successfully")
        return True

    def write_version_file(self) -> None:
        """Write version.txt with installed GAMMA version."""
        if not self.config.gamma_path:
            return

        version_file = self.config.gamma_path / '..' / 'version.txt'

        try:
            # Try to get GAMMA version from Git tag
            gamma_repo = self.config.gamma_path / 'Stalker_GAMMA'
            result = subprocess.run(
                ['git', '-C', str(gamma_repo), 'describe', '--tags', '--always'],
                capture_output=True,
                text=True,
                check=False
            )

            version = result.stdout.strip() if result.returncode == 0 else "unknown"

            with open(version_file, 'w') as f:
                f.write(version)

            self.config.installed_version = version
            logger.info(f"Version file written: {version}")

        except Exception as e:
            logger.warning(f"Could not write version file: {e}")

    def install(
        self,
        skip_anomaly: bool = False,
        skip_mo2: bool = False
    ) -> bool:
        """
        Execute complete GAMMA installation.

        Args:
            skip_anomaly: Skip Anomaly installation if already valid
            skip_mo2: Skip MO2 installation if already valid

        Returns:
            True if installation successful

        Raises:
            GammaInstallerError: If critical installation step fails
        """
        logger.info("Starting GAMMA installation")

        self.state.start_time = datetime.now()
        self._update_state(
            phase=InstallationPhase.CHECKING_REQUIREMENTS,
            overall_progress=0.0
        )

        try:
            # Phase 1: Check requirements
            if not self.check_requirements():
                raise GammaInstallerError("Requirements check failed")

            # Phase 2: Install Anomaly
            if not skip_anomaly or not self.anomaly_installer.verify_installation(self.config.anomaly_path):
                self._update_state(
                    phase=InstallationPhase.DOWNLOADING_ANOMALY,
                    operation="Downloading S.T.A.L.K.E.R. Anomaly 1.5.3...",
                    overall_progress=0.05
                )

                wine_mode = self.detect_wine()
                logger.info(f"Wine mode: {wine_mode}")

                def anomaly_download_progress(downloaded, total):
                    progress = downloaded / total if total > 0 else 0
                    self._update_state(
                        operation=f"Downloading Anomaly... ({downloaded // (1024**2)}MB / {total // (1024**2)}MB)",
                        phase_progress=progress,
                        overall_progress=0.05 + (progress * 0.05)
                    )

                def anomaly_extract_progress(extracted, total):
                    progress = extracted / total if total > 0 else 0
                    self._update_state(
                        phase=InstallationPhase.EXTRACTING_ANOMALY,
                        operation=f"Extracting Anomaly... ({extracted} / {total} files)",
                        phase_progress=progress,
                        overall_progress=0.10 + (progress * 0.05)
                    )

                self.anomaly_installer.install(
                    anomaly_path=self.config.anomaly_path,
                    cache_path=self.config.cache_path,
                    download_progress=anomaly_download_progress,
                    extract_progress=anomaly_extract_progress,
                    skip_if_valid=skip_anomaly,
                    wine_mode=wine_mode
                )

            # Phase 3: Install MO2
            if not skip_mo2 or not self.mo2_manager.verify_installation(self.config.gamma_path / '..'):
                self._update_state(
                    phase=InstallationPhase.DOWNLOADING_MO2,
                    operation="Downloading ModOrganizer2...",
                    overall_progress=0.15
                )

                def mo2_download_progress(downloaded, total):
                    progress = downloaded / total if total > 0 else 0
                    self._update_state(
                        operation=f"Downloading MO2... ({downloaded // (1024**2)}MB / {total // (1024**2)}MB)",
                        phase_progress=progress,
                        overall_progress=0.15 + (progress * 0.03)
                    )

                def mo2_extract_progress(extracted, total):
                    progress = extracted / total if total > 0 else 0
                    self._update_state(
                        operation=f"Extracting MO2... ({extracted} / {total} files)",
                        phase_progress=progress,
                        overall_progress=0.18 + (progress * 0.02)
                    )

                mo2_root = self.config.gamma_path / '..'

                self.mo2_manager.install(
                    mo2_root=mo2_root,
                    anomaly_path=self.config.anomaly_path,
                    cache_path=self.config.cache_path,
                    version=self.config.mo2_version,
                    download_progress=mo2_download_progress,
                    extract_progress=mo2_extract_progress,
                    skip_if_valid=skip_mo2
                )

            # Phase 4: Clone GAMMA repositories
            if not self.clone_gamma_repos():
                raise GammaInstallerError("Failed to clone GAMMA repositories")

            # Phase 5: Download and install mods
            self._update_state(
                phase=InstallationPhase.DOWNLOADING_MODS,
                operation="Parsing mod lists...",
                overall_progress=0.25
            )

            # Parse modlist and maker list
            gamma_repo = self.config.gamma_path / 'Stalker_GAMMA'
            modlist_path = gamma_repo / 'modlist.txt'
            maker_list_path = gamma_repo / 'modpack_maker_list.txt'

            enabled_mods = self.mod_manager.parse_modlist(modlist_path)
            mod_records = self.mod_manager.parse_mod_maker_list(maker_list_path, enabled_mods)

            self.state.total_mods = len([m for m in mod_records if m.enabled])

            def download_progress(mod_name, downloaded, total, completed):
                self.state.current_file = mod_name
                self.state.current_file_size = total
                self.state.current_file_progress = downloaded / total if total > 0 else 0
                self.state.downloaded_mods = completed

                progress = completed / self.state.total_mods if self.state.total_mods > 0 else 0
                self._update_state(
                    operation=f"Downloading {mod_name}... ({completed}/{self.state.total_mods})",
                    phase_progress=progress,
                    overall_progress=0.25 + (progress * 0.35)
                )

            def install_progress(mod_name, extracted, total, completed):
                self.state.current_file = mod_name
                self.state.installed_mods = completed

                progress = completed / self.state.total_mods if self.state.total_mods > 0 else 0
                self._update_state(
                    phase=InstallationPhase.EXTRACTING_MODS,
                    operation=f"Installing {mod_name}... ({completed}/{self.state.total_mods})",
                    phase_progress=progress,
                    overall_progress=0.60 + (progress * 0.25)
                )

            def status_update(message):
                self._update_state(operation=message)

            mods_dir = self.config.gamma_path / 'mods'
            mods_dir.mkdir(parents=True, exist_ok=True)

            successful, failed, failed_names = self.mod_manager.install_mods_parallel(
                mods=mod_records,
                cache_dir=self.config.cache_path,
                mods_dir=mods_dir,
                download_progress_callback=download_progress,
                install_progress_callback=install_progress,
                status_callback=status_update
            )

            self.state.failed_mods = failed_names

            if failed > 0:
                self._add_warning(f"{failed} mods failed to install")

            # Phase 6: Generate modlist.txt for MO2
            self._update_state(
                phase=InstallationPhase.CONFIGURING_MO2,
                operation="Configuring ModOrganizer2...",
                overall_progress=0.90
            )

            mo2_root = self.config.gamma_path / '..'
            profile_dir = mo2_root / 'profiles' / 'GAMMA'

            # Get final mod names (installed mods + separators)
            final_mod_names = [
                m.mod_name for m in mod_records
                if m.enabled and (m.mod_name not in failed_names)
            ]

            self.mo2_manager.generate_modlist(profile_dir, final_mod_names)

            # Phase 7: Finalize
            self._update_state(
                phase=InstallationPhase.FINALIZING,
                operation="Finalizing installation...",
                overall_progress=0.95
            )

            self.write_version_file()

            # Mark as completed
            self.state.end_time = datetime.now()
            self._update_state(
                phase=InstallationPhase.COMPLETED,
                operation="Installation complete!",
                overall_progress=1.0
            )

            elapsed = self.state.get_elapsed_time()
            logger.info(f"GAMMA installation complete in {self.state.format_time(elapsed)}")

            return True

        except (AnomalyError, MO2Error, ModManagerError, GammaInstallerError) as e:
            self.state.end_time = datetime.now()
            self._update_state(phase=InstallationPhase.FAILED)
            self._add_error(f"Installation failed: {e}")
            return False

        except Exception as e:
            self.state.end_time = datetime.now()
            self._update_state(phase=InstallationPhase.FAILED)
            self._add_error(f"Unexpected error: {e}")
            logger.exception("Unexpected error during installation")
            return False


import os  # Import for Wine detection
