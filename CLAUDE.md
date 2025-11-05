# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AOEngine Tools is a Python-based project containing three GUI applications for managing releases and installations:

1. **GAMMA Launcher**: End-user application for installing S.T.A.L.K.E.R. G.A.M.M.A. modpack with optional AOEngine integration. Downloads Anomaly 1.5.3 from ModDB, sets up GAMMA structure, installs ModOrganizer 2, and can launch AOEngine Launcher after completion.

2. **AOEngine Launcher**: End-user application for installing, updating, and managing AOEngine files with redundant fallback system for high availability

3. **Uploader**: Developer-only tool for creating mirrored releases across multiple hosting platforms (GitHub Releases, Catbox) and maintaining a version-controlled index

All applications are built with CustomTkinter GUI framework and packaged as standalone executables using PyInstaller.

## Build Commands

### Build Executables
```bash
# Build GAMMA Launcher executable
build_gamma_launcher.bat

# Build AOEngine Launcher executable
build_launcher.bat

# Build Uploader executable
build_uploader.bat
```

### Run in Development
```bash
# Run GAMMA Launcher (development mode)
python run_gamma_launcher_main.py

# Run AOEngine Launcher (development mode)
python run_launcher_main.py

# Run Uploader (development mode)
python run_uploader_main.py
```

### Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt
```

## Architecture Overview

### Core Architectural Pattern: Provider-Based System

The project uses a **provider architecture** with two distinct provider types:

- **Index Provider** (`GitHubGitProvider`): Manages the canonical `versions.json` file and release manifests in a Git repository. This ensures atomic, version-controlled updates for all critical metadata. Fixed to Git for reliability.

- **Asset Providers** (`GitHubReleaseProvider`, `CatboxProvider`): Handle uploading/downloading large binary files. Selectable and redundant - if one provider fails, the system automatically tries the next. Implements fallback logic with retries.

### Fallback and Redundancy System

Both applications implement a robust fallback mechanism:

1. Each downloadable resource (manifests, archives) has multiple URLs from different providers
2. URLs are stored as dictionaries: `{"GitHub Git": "url1", "Catbox": "url2"}`
3. Download attempts iterate through URLs in order (GitHub Git prioritized)
4. On failure (timeout, HTTP error >= 400), immediately tries next URL
5. Retries each URL up to 3 times before moving to the next provider

See `launcher/core/network.py:download_file_with_fallback()` and `launcher/core/network.py:_get_sorted_urls()` for implementation.

### Data Flow: Uploader to Launcher

**Uploader creates:**
1. Packages files into `.tar.zst` archive (zstandard compressed tarball)
2. Calculates SHA256 hash of archive
3. Creates `manifest-v<VERSION>.json` with metadata
4. Uploads archive and manifest to all selected asset providers in parallel
5. Commits canonical manifest to Git index repository
6. Updates `versions.json` in Git with URLs from all successful uploads

**Launcher consumes:**
1. Fetches `versions.json` from hardcoded GitHub URL
2. Finds version marked with `"latest": true`
3. Downloads manifest using fallback logic on `manifest_urls` dictionary
4. Downloads archive using fallback logic on `download_urls` dictionary
5. Verifies SHA256 hash from manifest against downloaded archive
6. Extracts `.tar.zst` using streaming decompression

See `LauncherDataSpec.md` for complete data structure specification.

### Shared Components

- **Localization System** (`shared/localization.py`): Global translator instance loaded from JSON locale files. Supports placeholder substitution. Uses `resource_path()` helper for PyInstaller compatibility.

- **Configuration Management**:
  - Launcher: Uses Pydantic models (`launcher/core/models.py`) and `ConfigManager` class (`launcher/core/config.py`) to persist `config.json`
  - Uploader: Uses `python-dotenv` to load `.env` file with provider credentials and settings

### Module Structure

```
launcher/
├── main.py                 # Entry point
├── core/
│   ├── config.py          # ConfigManager class for config.json persistence
│   ├── models.py          # Pydantic models: Config, Version, Manifest, ReleaseInfo
│   ├── network.py         # NetworkManager with download fallback logic
│   └── backup.py          # Backup/restore system
├── gui/
│   └── main_window.py     # Main application window
└── utils/
    └── logging.py         # Logging configuration

uploader/
├── main.py                # Entry point with TkinterDnD setup
├── config.py              # Settings class loading from .env
├── core/
│   └── workflow.py        # ReleaseWorkflow orchestrating entire release process
├── gui/
│   └── main_window.py     # Tabbed interface (Upload, Manage, Settings)
└── providers/
    ├── base.py            # Abstract base classes
    ├── github_git.py      # Index provider (Git operations)
    ├── github_release.py  # Asset provider (GitHub Releases API)
    └── catbox.py          # Asset provider (Catbox.moe API)

shared/
└── localization.py        # Shared localization system
```

## Key Implementation Details

### Archive Format
- Uses `.tar.zst` (zstandard compressed tarball) for maximum compression
- Compression level: 9 (maximum)
- Streaming extraction in launcher to handle large files efficiently
- See `uploader/core/workflow.py:_create_archive()` and `launcher/core/network.py:extract_archive()`

### Parallel Operations
- Uploader: Uploads to multiple asset providers in parallel using `ThreadPoolExecutor`
- Launcher: Downloads manifests for all versions in parallel when building release table
- Thread-safe queue-based system for status updates to GUI

### Version Selection
- `versions.json` is a JSON array (not object) with releases ordered newest first
- Only one release can have `"latest": true` at a time
- Launcher supports installing any historical version (downgrade capability)

### Backup System (Launcher)
- Initial backup: `launcher_backups/initial_vanilla_files/` created on first install
- Update backups: `launcher_backups/v1.2.0_2023-11-01_10-30-00/` with version and timestamp
- Manual restore via GUI

### Git Operations (Uploader)
- Index provider maintains local clone in `_index_repo_data` directory
- Always pulls before modifying to avoid conflicts
- Commits both manifest files and `versions.json` atomically
- Manifest files stored in `manifests/` subdirectory

### PyInstaller Packaging
- `--onefile`: Single executable
- `--noconsole`: No console window (GUI only)
- `--collect-data`: Bundles CustomTkinter and tkinter data files
- `--add-data`: Includes locale files and assets
- Multiple `--hidden-import` flags for dynamic imports

## Important Patterns

### Error Handling
- All network operations log errors and update GUI status
- Provider failures are logged but don't stop the entire process if one provider succeeds
- File operations wrapped in try-except with specific error messages

### Pydantic Models (Launcher)
- All configuration and API data structures use Pydantic for validation
- `model_dump()` for serialization
- `model_validate_json()` for parsing JSON strings
- `model_copy(update=kwargs)` for creating updated copies

### Resource Paths for PyInstaller
- Use `resource_path()` helper in `shared/localization.py` to resolve paths
- Checks for `sys._MEIPASS` attribute (PyInstaller temporary folder)
- Falls back to current working directory in development

### Status Callbacks
- All long-running operations accept optional `status_callback` for real-time GUI updates
- Progress callbacks report float 0.0-1.0 for progress bars
- Always report 1.0 at completion to ensure 100% display

## Testing and Development

### Running Without Building
Use `run_launcher_main.py` and `run_uploader_main.py` as entry points to avoid module resolution issues when running directly.

### Configuration Files
- Launcher: `config.json` auto-created on first run
- Uploader: Requires `.env` file with provider credentials (see `uploader/README.md` for template)

### Locale Files
- Located in `launcher/locale/` and `uploader/locale/`
- JSON format with key-value pairs
- Currently supports: en (English), ru (Russian)
