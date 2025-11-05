import logging
from pathlib import Path
from typing import Callable, Optional
import subprocess
import sys

from gamma_launcher.core.models import GammaConfig, InstallProgress
from gamma_launcher.core.anomaly_installer import AnomalyInstaller
from gamma_launcher.core.gamma_installer import GammaInstaller


class GammaWorkflow:
    """Orchestrates the complete GAMMA installation workflow."""

    def __init__(self, config: GammaConfig):
        self.config = config
        self.anomaly_installer = AnomalyInstaller()
        self.gamma_installer = GammaInstaller()

    def full_install(
        self,
        progress_callback: Optional[Callable[[InstallProgress], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """Performs complete GAMMA installation workflow."""
        try:
            anomaly_path = self.config.get_anomaly_path_obj()
            gamma_path = self.config.get_gamma_path_obj()
            cache_path = self.config.get_cache_path_obj()

            if not anomaly_path or not gamma_path:
                logging.error("Anomaly and Gamma paths must be configured")
                if status_callback:
                    status_callback("ERROR: Paths not configured")
                return False

            total_stages = 5
            current_stage = 0

            def update_progress(stage: str, fraction: float):
                if progress_callback:
                    progress = InstallProgress(
                        stage=stage,
                        current_step=current_stage,
                        total_steps=total_stages,
                        progress_fraction=fraction
                    )
                    progress_callback(progress)

            # Stage 1: Install Anomaly if needed
            current_stage = 1
            if not self.anomaly_installer.verify(anomaly_path):
                logging.info("Anomaly not found, installing...")
                if status_callback:
                    status_callback("Installing S.T.A.L.K.E.R.: Anomaly 1.5.3")
                
                self.anomaly_installer.install(
                    anomaly_path,
                    cache_path,
                    progress_callback=lambda f: update_progress("anomaly", f),
                    status_callback=status_callback
                )
            else:
                logging.info("Anomaly already installed, skipping")
                if status_callback:
                    status_callback("Anomaly already installed")

            # Stage 2: Install ModOrganizer
            current_stage = 2
            if self.config.install_mod_organizer:
                logging.info("Installing ModOrganizer")
                if status_callback:
                    status_callback("Installing ModOrganizer")
                
                self.gamma_installer.install_mod_organizer(
                    gamma_path,
                    version=self.config.mod_organizer_version,
                    cache_path=cache_path,
                    progress_callback=lambda f: update_progress("mod_organizer", f),
                    status_callback=status_callback
                )

            # Stage 3: Setup GAMMA structure
            current_stage = 3
            logging.info("Setting up GAMMA folder structure")
            if status_callback:
                status_callback("Setting up GAMMA structure")
            
            self.gamma_installer.setup_gamma_structure(
                gamma_path,
                cache_path,
                gamma_repo=self.config.custom_gamma_repo,
                progress_callback=lambda f: update_progress("gamma_setup", f),
                status_callback=status_callback
            )

            # Stage 4: Patch Anomaly
            current_stage = 4
            logging.info("Patching Anomaly directory")
            if status_callback:
                status_callback("Patching Anomaly with GAMMA files")
            
            self.gamma_installer.patch_anomaly(
                anomaly_path,
                gamma_path,
                status_callback=status_callback
            )

            # Stage 5: Create ModOrganizer profile
            current_stage = 5
            logging.info("Creating ModOrganizer profile")
            if status_callback:
                status_callback("Creating ModOrganizer profile")
            
            self.gamma_installer.create_mod_organizer_profile(
                gamma_path,
                status_callback=status_callback
            )

            if progress_callback:
                progress = InstallProgress(
                    stage="complete",
                    current_step=total_stages,
                    total_steps=total_stages,
                    progress_fraction=1.0
                )
                progress_callback(progress)

            logging.info("GAMMA installation complete!")
            if status_callback:
                status_callback("GAMMA installation complete!")

            return True

        except Exception as e:
            logging.error(f"Installation failed: {e}", exc_info=True)
            if status_callback:
                status_callback(f"ERROR: {str(e)}")
            return False

    def launch_ao_launcher(self) -> bool:
        """Attempts to launch AOLauncher if present."""
        ao_launcher_paths = [
            Path.cwd() / "AOLauncher.exe",
            Path.cwd() / "launcher" / "AOLauncher.exe",
            Path(sys.executable).parent / "AOLauncher.exe"
        ]

        for launcher_path in ao_launcher_paths:
            if launcher_path.exists():
                logging.info(f"Launching AOLauncher from {launcher_path}")
                try:
                    subprocess.Popen([str(launcher_path)], cwd=launcher_path.parent)
                    return True
                except Exception as e:
                    logging.error(f"Failed to launch AOLauncher: {e}")
                    return False

        logging.warning("AOLauncher not found")
        return False
