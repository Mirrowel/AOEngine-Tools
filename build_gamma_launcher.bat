@echo off
python -m PyInstaller --noconfirm --onefile --windowed ^
    --name "GAMMALauncher" ^
    --add-data "gamma_launcher/locale;gamma_launcher/locale" ^
    --add-data "gamma_launcher/assets;gamma_launcher/assets" ^
    --add-data "shared;shared" ^
    --hidden-import "customtkinter" ^
    run_gamma_launcher_main.py
