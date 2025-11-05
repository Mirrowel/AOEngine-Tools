# AOEngine Tools

This project contains tools for managing AOEngine releases and installing the S.T.A.L.K.E.R. G.A.M.M.A. modpack.

## Components

### 1. [GAMMA Launcher](./gamma_launcher/README.md)
A standalone GUI application for installing the S.T.A.L.K.E.R. G.A.M.M.A. modpack with optional AOEngine integration.

**Features:**
- Install S.T.A.L.K.E.R.: Anomaly 1.5.3 base game
- Setup G.A.M.M.A. modpack structure and files
- Install ModOrganizer 2 for mod management
- Patch Anomaly with G.A.M.M.A.-specific files
- Optional automatic launch of AOEngine Launcher after installation
- Multi-language support (English, Russian)
- Beautiful Fly Agaric theme

### 2. [AOEngine Launcher](./launcher/README.md)
End-user application for installing, updating, and managing AOEngine files with redundant fallback system for high availability.

**Features:**
- Install and update AOEngine releases
- Version management with downgrade support
- Automatic backup system
- Multi-language support
- SHA256 verification

### 3. [Uploader](./uploader/README.md)
Developer-only GUI application for creating mirrored software releases across multiple hosting platforms.

**Features:**
- Multi-provider upload (GitHub Releases, Catbox)
- Git-based index management
- Parallel uploads with retry logic
- Release management interface

## Quick Start

### For End Users

#### Install GAMMA + AOEngine
1. Run `run_gamma_launcher.bat` (or execute `python run_gamma_launcher_main.py`)
2. Set Anomaly and GAMMA installation paths
3. Click "Install GAMMA + AOEngine"
4. Follow the on-screen instructions

#### Install AOEngine Only
1. Run `run_launcher.bat` (or execute `python run_launcher_main.py`)
2. Set game path
3. Click "Install" or "Update"

### For Developers

#### Build Executables
```bash
# Build GAMMA Launcher
build_gamma_launcher.bat

# Build AOEngine Launcher
build_launcher.bat

# Build Uploader
build_uploader.bat
```

#### Requirements
```bash
pip install -r requirements.txt
```

## Overview

This repository is structured to support three complementary applications:

1. **GAMMA Launcher**: Installs the G.A.M.M.A. modpack foundation (Anomaly + GAMMA structure)
2. **AOEngine Launcher**: Manages AOEngine releases (can be launched from GAMMA Launcher)
3. **Uploader**: Developer tool for creating and managing releases

All three applications share:
- Consistent visual theme (Fly Agaric colors)
- Localization system
- Common utilities and patterns
- Professional logging and error handling

## Credits

**Developed by:** Mirrowel

**Based on:**
- [gamma-launcher](https://github.com/Mord3rca/gamma-launcher) by Mord3rca
- [stalker-gamma-launcher-clone](https://github.com/FaithBeam/stalker-gamma-launcher-clone) by FaithBeam

**Special Thanks:**
- Grokitach and contributors for the G.A.M.M.A. modpack
- Anomaly Development Team for S.T.A.L.K.E.R.: Anomaly
- The S.T.A.L.K.E.R. modding community

## License

This project combines multiple open-source components. See individual component directories for specific licensing information.
