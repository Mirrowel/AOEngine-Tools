# GAMMA Launcher

A standalone Python & CustomTkinter application that simplifies the installation of the S.T.A.L.K.E.R. G.A.M.M.A. modpack and integrates with the AOEngine Launcher.

## Highlights

- Guided installation flow for S.T.A.L.K.E.R.: Anomaly 1.5.3
- Automated setup of the G.A.M.M.A. modpack structure
- ModOrganizer 2 bootstrap with customizable version
- One-click patching of the Anomaly directory for G.A.M.M.A.
- Optional automatic launch of the AOEngine Launcher after completion
- English and Russian localization
- Fly Agaric themed UI matching AOEngine tools family
- Real-time console view and persistent logs

## Requirements

- Python 3.10+
- Windows, Linux, or macOS
- Stable internet connection
- ~120 GB free disk space for full G.A.M.M.A. installation

Install dependencies:
```bash
pip install -r ../requirements.txt
```

## Usage

### Development Mode
```bash
python ../run_gamma_launcher_main.py
```

### Packaged Executable (Windows)
```bash
build_gamma_launcher.bat
```
The compiled executable will be available in the `dist/` folder.

## Installation Flow

1. **Configure Paths**
   - Anomaly installation directory
   - G.A.M.M.A. installation directory
   - Optional shared cache directory

2. **Select Installation Mode**
   - Install GAMMA only
   - Install GAMMA and then launch AOEngine Launcher

3. **Follow Progress**
   - Real-time progress bar and status updates
   - Console window with detailed logs

4. **Completion Options**
   - Launch AOEngine Launcher (if available)
   - Open ModOrganizer 2 from the GAMMA directory

## Localization

Localization files are located in `./locale/`. To add a new language:
1. Duplicate `en.json`
2. Translate the values
3. Add the language code to the `language_option_menu` value list in `gui/main_window.py`

## Credits

- **Project Lead & Implementation:** Mirrowel
- **Original Python GAMMA Launcher:** Mord3rca
- **G.A.M.M.A. Modpack:** Grokitach & contributors
- **S.T.A.L.K.E.R.: Anomaly:** Anomaly Development Team

## License

This launcher integrates open-source components. Consult the root project licenses for compliance requirements.
