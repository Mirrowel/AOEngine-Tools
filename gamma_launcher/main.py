from gamma_launcher.gui.main_window import App
from gamma_launcher.utils.logging import setup_logging


def main():
    setup_logging()
    app = App()
    app.mainloop()
