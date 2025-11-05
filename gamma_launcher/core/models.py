from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path


class GammaConfig(BaseModel):
    """Configuration for Gamma Launcher."""
    anomaly_path: Optional[str] = None
    gamma_path: Optional[str] = None
    cache_path: Optional[str] = None
    mod_organizer_version: str = "v2.4.4"
    language: str = "en"
    install_mod_organizer: bool = True
    custom_gamma_repo: str = "Grokitach/Stalker_GAMMA"
    custom_gamma_definition: Optional[str] = None
    
    def get_anomaly_path_obj(self) -> Optional[Path]:
        return Path(self.anomaly_path) if self.anomaly_path else None
    
    def get_gamma_path_obj(self) -> Optional[Path]:
        return Path(self.gamma_path) if self.gamma_path else None
    
    def get_cache_path_obj(self) -> Optional[Path]:
        return Path(self.cache_path) if self.cache_path else None


class ModInfo(BaseModel):
    """Information about a mod to be downloaded and installed."""
    name: str
    url: str
    author: Optional[str] = None
    title: Optional[str] = None
    add_dirs: Optional[list[str]] = None
    info_url: Optional[str] = None


class InstallProgress(BaseModel):
    """Progress information for installation."""
    stage: str  # anomaly, gamma_setup, mods, patching, complete
    current_step: int = 0
    total_steps: int = 0
    current_file: str = ""
    progress_fraction: float = 0.0
