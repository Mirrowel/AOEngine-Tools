# GAMMA + AOEngine Installation Guide

## Overview

This guide will help you install S.T.A.L.K.E.R. G.A.M.M.A. modpack with optional AOEngine integration using the GAMMA Launcher.

## What is GAMMA?

G.A.M.M.A. (Great Anomaly Massive Modpack Alliance) is a comprehensive modpack for S.T.A.L.K.E.R.: Anomaly that combines hundreds of mods to create an enhanced experience with improved graphics, gameplay mechanics, and content.

## What is AOEngine?

AOEngine is a performance optimization and enhancement engine for S.T.A.L.K.E.R. games, providing improved stability and additional features.

## Requirements

### System Requirements
- **OS:** Windows 10/11, Linux (via Wine/Proton), macOS (via CrossOver)
- **CPU:** Modern multi-core processor (4+ cores recommended)
- **RAM:** 8 GB minimum, 16 GB+ recommended
- **Storage:** ~120 GB free space for complete installation
  - Anomaly: ~30 GB
  - GAMMA files: ~60 GB
  - Cache/temp: ~30 GB
- **Internet:** Stable broadband connection (will download ~40-60 GB)

### Software Requirements
- Python 3.10 or newer (for development mode)
- OR pre-built executable (no Python required)

## Installation Steps

### Method 1: Using Pre-built Executable (Recommended)

1. **Download GAMMA Launcher**
   - Download `GAMMALauncher.exe` from releases
   - Place it in a dedicated folder (e.g., `C:\GAMMA_Tools`)

2. **Launch the Application**
   - Double-click `GAMMALauncher.exe`
   - The application will open with a welcome screen

3. **Configure Paths**
   - **Anomaly Path:** Where S.T.A.L.K.E.R.: Anomaly will be installed
     - Example: `C:\Games\Anomaly`
     - Must have ~30 GB free space
   
   - **GAMMA Path:** Where GAMMA modpack files will be stored
     - Example: `C:\Games\GAMMA`
     - Must have ~60 GB free space
     - Can be on a different drive
   
   - **Cache Path (Optional):** Shared cache for downloads
     - Example: `D:\GAMMA_Cache`
     - Keeps downloaded files for re-use
     - Saves bandwidth if reinstalling

4. **Choose Installation Mode**

   **Option A: Install GAMMA Only**
   - Click "Install GAMMA Only"
   - Installs Anomaly + GAMMA modpack
   - You can manually launch AOEngine Launcher later

   **Option B: Install GAMMA + AOEngine**
   - Click "Install GAMMA + AOEngine"
   - Installs Anomaly + GAMMA modpack
   - Automatically launches AOEngine Launcher when done
   - Requires AOLauncher.exe in the same directory

5. **Monitor Installation Progress**
   - Progress bar shows current operation
   - Status messages appear in the text area
   - Open "Console" button for detailed logs
   - Installation takes 1-3 hours depending on internet speed

6. **Installation Stages**
   - **Stage 1:** Installing Anomaly 1.5.3 (~15-30 min)
   - **Stage 2:** Installing ModOrganizer 2 (~2-5 min)
   - **Stage 3:** Setting up GAMMA structure (~5-10 min)
   - **Stage 4:** Patching Anomaly directory (~2-5 min)
   - **Stage 5:** Creating ModOrganizer profile (~1-2 min)

7. **After Installation**
   - If you chose GAMMA + AOEngine, the AOEngine Launcher will open
   - Follow AOEngine installation instructions
   - Navigate to your GAMMA directory
   - Launch `ModOrganizer.exe`
   - Set the Anomaly path in ModOrganizer (Tools → Settings → Paths)
   - Select the "G.A.M.M.A" profile
   - Click "Run" to start the game

### Method 2: Using Python (Development Mode)

1. **Install Python**
   - Download Python 3.10+ from python.org
   - Ensure "Add Python to PATH" is checked during installation

2. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd AOEngine-Tools
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run GAMMA Launcher**
   ```bash
   python run_gamma_launcher_main.py
   ```

5. **Follow steps 3-7 from Method 1**

## Settings

Access Settings by clicking the "Settings" button:

### ModOrganizer Version
- Default: `v2.4.4`
- Change if you need a specific version
- Format: `v2.4.4`, `v2.5.0`, etc.

### Install ModOrganizer
- Checkbox to enable/disable MO2 installation
- Disable if you already have MO2 installed elsewhere

### GAMMA Repository
- Default: `Grokitach/Stalker_GAMMA`
- Change if using a custom fork
- Format: `Owner/Repository`

### Language
- English or Russian
- Changes all UI text
- Saved in configuration

## Troubleshooting

### Installation Fails to Download Anomaly
- **Cause:** ModDB download issues or slow connection
- **Solution:** 
  - Check internet connection
  - Try again later (ModDB can be busy)
  - Check console logs for specific error
  - Consider downloading Anomaly manually and extracting to the Anomaly path

### Not Enough Disk Space
- **Cause:** Insufficient free space on target drive
- **Solution:**
  - Free up space on target drives
  - Use different drives for Anomaly and GAMMA paths
  - Use cache path on drive with more space

### "AOEngine Launcher Not Found"
- **Cause:** AOLauncher.exe not in same directory
- **Solution:**
  - Build AOLauncher using `build_launcher.bat`
  - Place `AOLauncher.exe` in same folder as `GAMMALauncher.exe`
  - Or manually launch AOLauncher after GAMMA installation

### ModOrganizer Won't Start Game
- **Cause:** Anomaly path not configured in MO2
- **Solution:**
  - Open ModOrganizer.exe
  - Go to Settings → Paths
  - Set the correct Anomaly installation path
  - Restart ModOrganizer

### Installation Hangs or Freezes
- **Cause:** Network timeout or corrupted download
- **Solution:**
  - Check console logs for error messages
  - Close and restart launcher
  - Clear cache directory and try again
  - Check antivirus/firewall settings

### Python Import Errors (Development Mode)
- **Cause:** Missing dependencies
- **Solution:**
  ```bash
  pip install --upgrade -r requirements.txt
  ```

## Post-Installation

### First Launch Checklist
1. Open ModOrganizer.exe from GAMMA directory
2. Verify Anomaly path is set correctly
3. Select "G.A.M.M.A" profile
4. Review mod list (should show all GAMMA mods)
5. Configure graphics settings (first launch)
6. Start game via ModOrganizer's "Run" button

### Optional: Install AOEngine
1. If not installed during GAMMA setup, launch `AOLauncher.exe`
2. Set game path to Anomaly installation
3. Click "Install" or "Update"
4. Wait for AOEngine to download and install
5. Launch game via ModOrganizer

### Updating GAMMA
- Re-run GAMMA Launcher with existing paths
- It will update GAMMA definition files
- Some mods may need manual updates via ModOrganizer

## Performance Tips

### Storage Optimization
- Use SSD for Anomaly installation (faster loading)
- Cache can be on HDD to save SSD space
- Enable cache path to avoid re-downloading files

### Network Optimization
- Use wired connection for stability
- Avoid peak hours for faster downloads
- Consider using download manager for large files

### System Optimization
- Close unnecessary background applications
- Disable antivirus temporarily during installation (re-enable after!)
- Ensure power settings are set to "High Performance"

## Support

### Getting Help
- **Console Logs:** Click "Console" button to view detailed logs
- **GitHub Issues:** Report bugs at the repository issues page
- **Discord:** Join the AOEngine Discord community
- **GAMMA Discord:** Join the official GAMMA Discord for modpack support

### Common Resources
- [Official GAMMA Guide](https://github.com/Grokitach/Stalker_GAMMA)
- [Anomaly Wiki](https://anomaly.fandom.com/wiki/S.T.A.L.K.E.R._Anomaly_Wiki)
- [ModOrganizer 2 Documentation](https://github.com/ModOrganizer2/modorganizer)

## Credits

- **GAMMA Launcher Developer:** Mirrowel
- **Based on:** gamma-launcher by Mord3rca
- **GAMMA Modpack:** Grokitach and contributors
- **S.T.A.L.K.E.R.: Anomaly:** Anomaly Development Team
- **Original S.T.A.L.K.E.R. Games:** GSC Game World

## License

This launcher is open-source. See individual component licenses for details.

---

**Good hunting, Stalker!** 🍄
