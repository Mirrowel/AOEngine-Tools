import logging
from pathlib import Path
from typing import Callable, Optional

from gamma_launcher.core.downloader import Downloader
from gamma_launcher.core.archive import ArchiveExtractor


ANOMALY_VERSION = "1.5.3"
ANOMALY_MODDB_DOWNLOAD_URL = "https://www.moddb.com/downloads/start/277404"
ANOMALY_MODDB_INFO_URL = "https://www.moddb.com/mods/stalker-anomaly/downloads/stalker-anomaly-153"


class AnomalyInstaller:
    """Handles installation of S.T.A.L.K.E.R.: Anomaly base game."""

    def __init__(self):
        self.downloader = Downloader()
        self.extractor = ArchiveExtractor()

    def install(
        self,
        anomaly_path: Path,
        cache_path: Optional[Path] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """Installs Anomaly 1.5.3 to the specified path."""
        logging.info(f"Installing Anomaly {ANOMALY_VERSION} to {anomaly_path}")
        
        if status_callback:
            status_callback(f"Installing Anomaly {ANOMALY_VERSION}")

        anomaly_path.mkdir(parents=True, exist_ok=True)
        
        if cache_path is None:
            cache_path = anomaly_path
        cache_path.mkdir(parents=True, exist_ok=True)
        
        archive_name = f"anomaly-{ANOMALY_VERSION}.7z"
        archive_path = cache_path / archive_name
        
        if not archive_path.exists():
            if status_callback:
                status_callback(f"Downloading Anomaly {ANOMALY_VERSION} from ModDB")
            
            try:
                download_link = self.downloader.get_moddb_download_link(
                    ANOMALY_MODDB_INFO_URL,
                    ANOMALY_MODDB_DOWNLOAD_URL
                )
                self.downloader.download_file(
                    download_link,
                    archive_path,
                    progress_callback=progress_callback,
                    status_callback=status_callback
                )
            except Exception as e:
                logging.error(f"Failed to download Anomaly: {e}")
                raise
        else:
            logging.info(f"Using cached Anomaly archive at {archive_path}")
            if status_callback:
                status_callback(f"Using cached Anomaly archive")

        if status_callback:
            status_callback(f"Extracting Anomaly to {anomaly_path}")
        
        self.extractor.extract(archive_path, anomaly_path)
        
        logging.info("Anomaly installation complete")
        if status_callback:
            status_callback("Anomaly installation complete")

    def verify(self, anomaly_path: Path) -> bool:
        """Verifies that Anomaly is properly installed."""
        bin_path = anomaly_path / "bin"
        if not bin_path.is_dir():
            return False
        
        required_exes = [
            bin_path / "AnomalyDX9.exe",
            bin_path / "AnomalyDX11.exe"
        ]
        
        return all(exe.is_file() for exe in required_exes)
