from .gui.launcher_selection import LauncherSelectionWindow
from .utils.logging import setup_logging
from shared.localization import init_translator
from .core.config import ConfigManager

def main():
    """Main entry point for the unified launcher."""
    setup_logging()

    # Initialize localization
    config_manager = ConfigManager()
    init_translator("launcher/locale", config_manager.get_config().language)

    # Show launcher selection screen
    app = LauncherSelectionWindow()
    app.mainloop()

# This block is removed to prevent execution when imported.
# The entry point is now handled by the runner script.