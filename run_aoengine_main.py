import sys
import os

# This ensures the 'launcher' package can be found
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == '__main__':
    from launcher.utils.logging import setup_logging
    from shared.localization import init_translator
    from launcher.core.config import ConfigManager
    from launcher.gui.main_window import App

    setup_logging()

    # Initialize localization
    config_manager = ConfigManager()
    init_translator("launcher/locale", config_manager.get_config().language)

    # Launch AOEngine launcher directly
    app = App()
    app.mainloop()
