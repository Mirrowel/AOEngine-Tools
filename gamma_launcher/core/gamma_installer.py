import logging
from pathlib import Path
from typing import Callable, Optional
import shutil
from tempfile import TemporaryDirectory

from gamma_launcher.core.downloader import Downloader
from gamma_launcher.core.archive import ArchiveExtractor


class GammaInstaller:
    """Handles installation of GAMMA modpack setup."""

    def __init__(self):
        self.downloader = Downloader()
        self.extractor = ArchiveExtractor()

    def install_mod_organizer(
        self,
        gamma_path: Path,
        version: str = "v2.4.4",
        cache_path: Optional[Path] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """Installs ModOrganizer 2 to the GAMMA directory."""
        logging.info(f"Installing ModOrganizer {version}")
        
        if status_callback:
            status_callback(f"Installing ModOrganizer {version}")

        url = f"https://github.com/ModOrganizer2/modorganizer/releases/download/{version}/Mod.Organizer-{version.lstrip('v')}.7z"
        
        if cache_path is None:
            cache_path = gamma_path
        cache_path.mkdir(parents=True, exist_ok=True)
        
        archive_name = f"ModOrganizer-{version}.7z"
        archive_path = cache_path / archive_name
        
        if not archive_path.exists():
            self.downloader.download_file(
                url,
                archive_path,
                progress_callback=progress_callback,
                status_callback=status_callback
            )
        else:
            logging.info(f"Using cached ModOrganizer archive at {archive_path}")

        if status_callback:
            status_callback("Extracting ModOrganizer")
        
        self.extractor.extract(archive_path, gamma_path)
        logging.info("ModOrganizer installation complete")

    def setup_gamma_structure(
        self,
        gamma_path: Path,
        cache_path: Optional[Path] = None,
        gamma_repo: str = "Grokitach/Stalker_GAMMA",
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """Sets up GAMMA folder structure and downloads definition files."""
        logging.info("Setting up GAMMA structure")
        
        if status_callback:
            status_callback("Setting up GAMMA folder structure")

        gamma_path.mkdir(parents=True, exist_ok=True)
        
        grok_mod_dir = gamma_path / ".Grok's Modpack Installer" / "G.A.M.M.A"
        grok_mod_dir.mkdir(parents=True, exist_ok=True)
        
        downloads_dir = gamma_path / "downloads"
        downloads_dir.mkdir(exist_ok=True)
        
        mods_dir = gamma_path / "mods"
        mods_dir.mkdir(exist_ok=True)
        
        if cache_path:
            cache_path.mkdir(parents=True, exist_ok=True)
        
        if status_callback:
            status_callback(f"Downloading GAMMA definition from {gamma_repo}")
        
        gamma_archive_path = downloads_dir / "gamma_setup.zip"
        
        self.downloader.download_github_release(
            f"https://github.com/Grokitach/gamma_setup",
            gamma_archive_path,
            branch="main",
            progress_callback=progress_callback,
            status_callback=status_callback
        )
        
        if status_callback:
            status_callback("Extracting GAMMA setup files")
        
        with TemporaryDirectory(prefix="gamma-setup-") as temp_dir:
            temp_path = Path(temp_dir)
            self.extractor.extract(gamma_archive_path, temp_path)
            
            extracted_folders = [f for f in temp_path.iterdir() if f.is_dir() and f.name.startswith("gamma_setup")]
            if extracted_folders:
                source_folder = extracted_folders[0]
                for item in source_folder.iterdir():
                    dest = grok_mod_dir / item.name
                    if item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)
        
        logging.info("GAMMA structure setup complete")
        if status_callback:
            status_callback("GAMMA structure setup complete")

    def patch_anomaly(
        self,
        anomaly_path: Path,
        gamma_path: Path,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """Patches Anomaly directory with GAMMA-specific files."""
        logging.info("Patching Anomaly with GAMMA files")
        
        if status_callback:
            status_callback("Patching Anomaly directory")

        grok_mod_dir = gamma_path / ".Grok's Modpack Installer" / "G.A.M.M.A"
        patches_dir = grok_mod_dir / "G.A.M.M.A" / "modpack_patches"
        
        if not patches_dir.exists():
            logging.warning(f"Patches directory not found at {patches_dir}")
            return
        
        user_config = anomaly_path / "appdata" / "user.ltx"
        if user_config.is_file():
            backup_config = anomaly_path / "appdata" / "user.ltx.bak"
            shutil.copy2(user_config, backup_config)
        
        shutil.copytree(patches_dir, anomaly_path, dirs_exist_ok=True)
        
        if user_config.is_file():
            content = user_config.read_text()
            content = content.replace("rs_screenmode fullscreen", "rs_screenmode borderless")
            user_config.write_text(content)
        
        logging.info("Anomaly patching complete")
        if status_callback:
            status_callback("Anomaly patching complete")

    def create_mod_organizer_profile(
        self,
        gamma_path: Path,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """Creates ModOrganizer profile for GAMMA."""
        logging.info("Creating ModOrganizer profile")
        
        if status_callback:
            status_callback("Creating ModOrganizer profile")

        profile_path = gamma_path / "profiles" / "G.A.M.M.A"
        profile_path.mkdir(parents=True, exist_ok=True)
        
        grok_mod_dir = gamma_path / ".Grok's Modpack Installer" / "G.A.M.M.A"
        modlist_source = grok_mod_dir / "G.A.M.M.A" / "modpack_data" / "modlist.txt"
        
        if modlist_source.exists():
            shutil.copy2(modlist_source, profile_path / "modlist.txt")
        
        settings_file = profile_path / "settings.txt"
        settings_file.write_text("""[General]
LocalSaves=false
LocalSettings=true
AutomaticArchiveInvalidation=false
""")
        
        logging.info("ModOrganizer profile created")
        if status_callback:
            status_callback("ModOrganizer profile created")
