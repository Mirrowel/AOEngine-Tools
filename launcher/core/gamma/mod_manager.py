"""
Mod Manager with Parallel Pipeline

Handles downloading and installing GAMMA mods with parallel processing.
Implements a two-phase pipeline: parallel downloads followed by parallel extractions.
"""

import logging
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Callable, Dict, Tuple
from queue import Queue

from .models import ModRecord, DownloadableModRecord, SeparatorRecord, ModType
from .moddb import ModDBDownloader, ModDBError
from .archive import ArchiveExtractor, ArchiveError, FOMODParser, detect_mod_structure

logger = logging.getLogger(__name__)


class ModManagerError(Exception):
    """Base exception for mod manager operations."""
    pass


class ModManager:
    """
    Manages mod downloads and installations with parallel processing.

    Implements a two-phase pipeline:
    1. Download Phase: Multiple parallel downloads from ModDB/GitHub
    2. Extraction Phase: Parallel archive extraction and file copying

    This approach maximizes throughput by overlapping network I/O and disk I/O.

    Attributes:
        downloader: ModDB downloader instance
        extractor: Archive extractor instance
        max_parallel_downloads: Maximum concurrent downloads
        max_parallel_extractions: Maximum concurrent extractions
    """

    def __init__(
        self,
        max_parallel_downloads: int = 4,
        max_parallel_extractions: int = 2
    ):
        """
        Initialize mod manager.

        Args:
            max_parallel_downloads: Max concurrent downloads (1-8)
            max_parallel_extractions: Max concurrent extractions (1-4)
        """
        self.downloader = ModDBDownloader()
        self.extractor = ArchiveExtractor()
        self.max_parallel_downloads = max(1, min(8, max_parallel_downloads))
        self.max_parallel_extractions = max(1, min(4, max_parallel_extractions))

    def parse_modlist(self, modlist_path: Path) -> List[str]:
        """
        Parse modlist.txt to get enabled mods.

        Format: Each line is +ModName (enabled) or -ModName (disabled)

        Args:
            modlist_path: Path to modlist.txt

        Returns:
            List of enabled mod names

        Raises:
            FileNotFoundError: If modlist.txt doesn't exist
        """
        if not modlist_path.exists():
            raise FileNotFoundError(f"Modlist not found: {modlist_path}")

        logger.info(f"Parsing modlist: {modlist_path}")

        enabled_mods = []

        with open(modlist_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Check if mod is enabled (+) or disabled (-)
                if line.startswith('+'):
                    mod_name = line[1:].strip()
                    enabled_mods.append(mod_name)

        logger.info(f"Found {len(enabled_mods)} enabled mods")
        return enabled_mods

    def parse_mod_maker_list(
        self,
        maker_list_path: Path,
        enabled_mods: Optional[List[str]] = None
    ) -> List[ModRecord]:
        """
        Parse modpack_maker_list.txt to get mod metadata.

        Args:
            maker_list_path: Path to modpack_maker_list.txt
            enabled_mods: List of enabled mod names (None = all enabled)

        Returns:
            List of ModRecord objects

        Raises:
            FileNotFoundError: If maker list doesn't exist
        """
        if not maker_list_path.exists():
            raise FileNotFoundError(f"Maker list not found: {maker_list_path}")

        logger.info(f"Parsing mod maker list: {maker_list_path}")

        mod_records = []

        with open(maker_list_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                try:
                    # Determine if mod is enabled
                    enabled = True
                    if enabled_mods is not None:
                        # For separators, always include
                        parts = line.split('\t')
                        if len(parts) >= 4:
                            mod_name = parts[3]
                            enabled = mod_name in enabled_mods

                    # Parse TSV line into ModRecord
                    record = ModRecord.from_tsv_line(line, enabled=enabled)
                    mod_records.append(record)

                except Exception as e:
                    logger.warning(f"Failed to parse line {line_num}: {e}")
                    continue

        enabled_count = sum(1 for r in mod_records if r.enabled)
        logger.info(f"Parsed {len(mod_records)} mods ({enabled_count} enabled)")

        return mod_records

    def download_mod(
        self,
        mod: DownloadableModRecord,
        cache_dir: Path,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> bool:
        """
        Download a single mod.

        Args:
            mod: Mod record to download
            cache_dir: Cache directory
            progress_callback: Called with (mod_name, bytes_downloaded, total_bytes)

        Returns:
            True if download successful, False otherwise
        """
        logger.info(f"Downloading mod: {mod.mod_name}")

        try:
            output_path = mod.get_cache_path(cache_dir)

            def download_progress(downloaded: int, total: int):
                if progress_callback:
                    progress_callback(mod.mod_name, downloaded, total)

            if mod.mod_type == ModType.MODDB:
                # ModDB download with scraping
                self.downloader.download_mod(
                    info_url=mod.info_url or "",
                    download_url=mod.url,
                    output_path=output_path,
                    expected_md5=mod.md5_hash,
                    progress_callback=download_progress,
                    use_cached=True
                )

            elif mod.mod_type == ModType.GITHUB:
                # GitHub direct download
                self.downloader.download_file(
                    url=mod.url,
                    output_path=output_path,
                    expected_md5=mod.md5_hash,
                    progress_callback=download_progress
                )

            else:
                logger.warning(f"Unsupported mod type: {mod.mod_type}")
                return False

            logger.info(f"Downloaded: {mod.mod_name}")
            return True

        except (ModDBError, Exception) as e:
            logger.error(f"Failed to download {mod.mod_name}: {e}")
            return False

    def extract_and_install_mod(
        self,
        mod: DownloadableModRecord,
        cache_dir: Path,
        mods_dir: Path,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> bool:
        """
        Extract and install a single mod.

        Args:
            mod: Mod record to install
            cache_dir: Cache directory
            mods_dir: MO2 mods directory
            progress_callback: Called with (mod_name, files_extracted, total_files)

        Returns:
            True if installation successful, False otherwise
        """
        logger.info(f"Installing mod: {mod.mod_name}")

        archive_path = mod.get_cache_path(cache_dir)
        if not archive_path.exists():
            logger.error(f"Archive not found for {mod.mod_name}: {archive_path}")
            return False

        try:
            # Create temporary extraction directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                def extract_progress(extracted: int, total: int):
                    if progress_callback:
                        progress_callback(mod.mod_name, extracted, total)

                # Extract archive
                self.extractor.extract(archive_path, temp_path, extract_progress)

                # Determine installation method
                installed = False

                # Check for FOMOD directives
                fomod_path = temp_path / 'fomod' / 'ModuleConfig.xml'
                if fomod_path.exists():
                    installed = self._install_with_fomod(mod, temp_path, mods_dir, fomod_path)

                # Check for custom instructions
                elif mod.instructions and mod.instructions != "0":
                    installed = self._install_with_instructions(mod, temp_path, mods_dir)

                # Auto-detect structure
                else:
                    installed = self._install_auto_detect(mod, temp_path, mods_dir)

                if installed:
                    # Create meta.ini
                    self._create_meta_ini(mod, mods_dir)

                logger.info(f"Installed: {mod.mod_name}")
                return installed

        except (ArchiveError, Exception) as e:
            logger.error(f"Failed to install {mod.mod_name}: {e}")
            return False

    def _install_with_fomod(
        self,
        mod: DownloadableModRecord,
        temp_path: Path,
        mods_dir: Path,
        fomod_path: Path
    ) -> bool:
        """Install mod using FOMOD directives."""
        logger.info(f"Installing {mod.mod_name} with FOMOD directives")

        try:
            directives = FOMODParser.parse_fomod(fomod_path)
            if not directives:
                # Fallback to auto-detect
                return self._install_auto_detect(mod, temp_path, mods_dir)

            install_path = mods_dir / mod.mod_name
            install_path.mkdir(parents=True, exist_ok=True)

            FOMODParser.apply_fomod_directives(temp_path, install_path, directives)

            return True

        except Exception as e:
            logger.error(f"FOMOD installation failed: {e}")
            return False

    def _install_with_instructions(
        self,
        mod: DownloadableModRecord,
        temp_path: Path,
        mods_dir: Path
    ) -> bool:
        """Install mod using custom instructions (colon-separated paths)."""
        logger.info(f"Installing {mod.mod_name} with custom instructions")

        try:
            install_path = mods_dir / mod.mod_name
            install_path.mkdir(parents=True, exist_ok=True)

            # Parse instructions (colon-separated folder paths)
            folders = mod.instructions.split(':')

            for folder in folders:
                folder = folder.strip()
                if not folder:
                    continue

                source = temp_path / folder
                if not source.exists():
                    logger.warning(f"Instruction folder not found: {folder}")
                    continue

                # Copy folder contents
                self._copy_directory(source, install_path)

            return True

        except Exception as e:
            logger.error(f"Instruction-based installation failed: {e}")
            return False

    def _install_auto_detect(
        self,
        mod: DownloadableModRecord,
        temp_path: Path,
        mods_dir: Path
    ) -> bool:
        """Install mod with automatic structure detection."""
        logger.info(f"Installing {mod.mod_name} with auto-detection")

        try:
            install_path = mods_dir / mod.mod_name
            install_path.mkdir(parents=True, exist_ok=True)

            # Detect mod structure
            mod_root = detect_mod_structure(temp_path)

            if mod_root:
                # Copy from detected root
                self._copy_directory(mod_root, install_path)
            else:
                # Copy everything
                self._copy_directory(temp_path, install_path)

            return True

        except Exception as e:
            logger.error(f"Auto-detect installation failed: {e}")
            return False

    def _copy_directory(self, source: Path, dest: Path) -> None:
        """Recursively copy directory contents."""
        for item in source.rglob('*'):
            if item.is_file():
                rel_path = item.relative_to(source)
                target = dest / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)

    def _create_meta_ini(self, mod: DownloadableModRecord, mods_dir: Path) -> None:
        """Create meta.ini for ModOrganizer."""
        mod_dir = mods_dir / mod.mod_name
        meta_ini = mod_dir / 'meta.ini'

        content = mod.generate_meta_ini(mod_dir)

        with open(meta_ini, 'w', encoding='utf-8') as f:
            f.write(content)

    def install_separator(
        self,
        separator: SeparatorRecord,
        mods_dir: Path,
        index: int
    ) -> bool:
        """
        Install a separator (folder divider in MO2).

        Args:
            separator: Separator record
            mods_dir: MO2 mods directory
            index: Separator index for naming

        Returns:
            True if successful
        """
        logger.info(f"Creating separator: {separator.mod_name}")

        try:
            # Create separator directory with index prefix
            sep_name = f"{index:03d}-{separator.mod_name}_separator"
            sep_dir = mods_dir / sep_name
            sep_dir.mkdir(parents=True, exist_ok=True)

            # Create meta.ini
            meta_ini = sep_dir / 'meta.ini'
            content = separator.generate_meta_ini(index)

            with open(meta_ini, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception as e:
            logger.error(f"Failed to create separator: {e}")
            return False

    def install_mods_parallel(
        self,
        mods: List[ModRecord],
        cache_dir: Path,
        mods_dir: Path,
        download_progress_callback: Optional[Callable[[str, int, int, int], None]] = None,
        install_progress_callback: Optional[Callable[[str, int, int, int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, int, List[str]]:
        """
        Install multiple mods with parallel processing.

        Implements two-phase pipeline:
        1. Download phase: Parallel downloads
        2. Installation phase: Parallel extraction and copying

        Args:
            mods: List of mod records
            cache_dir: Cache directory
            mods_dir: MO2 mods directory
            download_progress_callback: Called with (mod_name, downloaded, total, completed_count)
            install_progress_callback: Called with (mod_name, extracted, total, completed_count)
            status_callback: Called with status messages

        Returns:
            Tuple of (successful_count, failed_count, failed_mod_names)
        """
        downloadable_mods = [m for m in mods if isinstance(m, DownloadableModRecord) and m.enabled]
        separators = [m for m in mods if isinstance(m, SeparatorRecord)]

        total_downloadable = len(downloadable_mods)
        total_separators = len(separators)

        logger.info(f"Installing {total_downloadable} downloadable mods and {total_separators} separators")

        successful = 0
        failed = 0
        failed_names = []

        # Phase 1: Download mods in parallel
        if status_callback:
            status_callback(f"Downloading {total_downloadable} mods...")

        downloaded_mods = []

        with ThreadPoolExecutor(max_workers=self.max_parallel_downloads) as executor:
            futures = {}

            for mod in downloadable_mods:
                def make_progress_callback(mod_name):
                    def callback(downloaded, total):
                        if download_progress_callback:
                            download_progress_callback(
                                mod_name,
                                downloaded,
                                total,
                                len(downloaded_mods)
                            )
                    return callback

                future = executor.submit(
                    self.download_mod,
                    mod,
                    cache_dir,
                    make_progress_callback(mod.mod_name)
                )
                futures[future] = mod

            # Wait for downloads
            for future in as_completed(futures):
                mod = futures[future]
                try:
                    success = future.result()
                    if success:
                        downloaded_mods.append(mod)
                    else:
                        failed += 1
                        failed_names.append(mod.mod_name)
                except Exception as e:
                    logger.error(f"Download error for {mod.mod_name}: {e}")
                    failed += 1
                    failed_names.append(mod.mod_name)

        logger.info(f"Downloaded {len(downloaded_mods)}/{total_downloadable} mods")

        # Phase 2: Install mods in parallel
        if status_callback:
            status_callback(f"Installing {len(downloaded_mods)} mods...")

        installed_count = 0

        with ThreadPoolExecutor(max_workers=self.max_parallel_extractions) as executor:
            futures = {}

            for mod in downloaded_mods:
                def make_progress_callback(mod_name):
                    def callback(extracted, total):
                        if install_progress_callback:
                            install_progress_callback(
                                mod_name,
                                extracted,
                                total,
                                installed_count
                            )
                    return callback

                future = executor.submit(
                    self.extract_and_install_mod,
                    mod,
                    cache_dir,
                    mods_dir,
                    make_progress_callback(mod.mod_name)
                )
                futures[future] = mod

            # Wait for installations
            for future in as_completed(futures):
                mod = futures[future]
                try:
                    success = future.result()
                    if success:
                        successful += 1
                        installed_count += 1
                    else:
                        failed += 1
                        failed_names.append(mod.mod_name)
                except Exception as e:
                    logger.error(f"Install error for {mod.mod_name}: {e}")
                    failed += 1
                    failed_names.append(mod.mod_name)

        # Phase 3: Install separators (sequential, fast)
        if status_callback:
            status_callback(f"Creating {total_separators} separators...")

        for i, separator in enumerate(separators):
            if self.install_separator(separator, mods_dir, i):
                successful += 1
            else:
                failed += 1
                failed_names.append(separator.mod_name)

        logger.info(f"Installation complete: {successful} successful, {failed} failed")

        return successful, failed, failed_names
