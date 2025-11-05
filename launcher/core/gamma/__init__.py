"""
GAMMA Installer Module

This module provides functionality for installing S.T.A.L.K.E.R. GAMMA modpack.
It handles downloading, extracting, and configuring the complete GAMMA installation
including Anomaly base game, ModOrganizer2, and all required mods.

Components:
    - installer: Main orchestrator for GAMMA installation
    - mod_manager: Handles mod downloads and installation
    - moddb: ModDB scraping and download functionality
    - archive: Archive extraction utilities
    - mo2: ModOrganizer2 setup and configuration
    - anomaly: Base Anomaly installation
    - models: Pydantic data models for GAMMA components
"""

from .models import (
    GammaConfig,
    ModType,
    ModRecord,
    SeparatorRecord,
    DownloadableModRecord,
    InstallationPhase,
    InstallationState,
)

__all__ = [
    'GammaConfig',
    'ModType',
    'ModRecord',
    'SeparatorRecord',
    'DownloadableModRecord',
    'InstallationPhase',
    'InstallationState',
]
