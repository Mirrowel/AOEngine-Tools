"""
Launcher Selection Screen - Professional Grid-Based Design

Complete redesign using grid layout for proper scaling at any window size.
Inspired by GAMMA launcher's successful architecture.
"""

import customtkinter as ctk
from tkinter import messagebox
import logging
from pathlib import Path

from shared.localization import get_translator
from launcher.core.config import ConfigManager

# Theme colors
FLY_AGARIC_RED = "#A52A2A"
FLY_AGARIC_WHITE = "#F9F6EE"
FLY_AGARIC_BLACK = "#2C1810"
GAMMA_BLUE = "#00A8E8"
GAMMA_ORANGE = "#FF6B35"


class LauncherSelectionWindow(ctk.CTk):
    """
    Professional launcher selection screen with grid-based scaling.

    Features:
    - Grid layout that scales properly at any size
    - Fixed-size content area that centers when expanded
    - Language selector
    - Professional appearance
    """

    def __init__(self):
        super().__init__()

        self.title("AOEngine Tools - Launcher Selection")
        self.geometry("700x450")
        self.minsize(700, 450)
        self.resizable(True, True)

        # Set up dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Config and translator
        self.config_manager = ConfigManager()
        self.translator = get_translator()

        # State
        self.sequential_mode = ctk.BooleanVar(value=False)

        self._create_widgets()

    def _create_widgets(self):
        """Creates and lays out all GUI widgets using grid."""
        # Configure root grid - center everything
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main container - fixed size, centered
        main_container = ctk.CTkFrame(
            self,
            fg_color=FLY_AGARIC_BLACK,
            border_color=FLY_AGARIC_RED,
            border_width=2,
            width=680,
            height=430
        )
        main_container.grid(row=0, column=0, sticky="")  # No sticky = centered
        main_container.grid_propagate(False)  # Maintain fixed size

        # Configure main container grid
        main_container.grid_rowconfigure(0, weight=0)  # Header
        main_container.grid_rowconfigure(1, weight=0)  # Subtitle
        main_container.grid_rowconfigure(2, weight=1)  # Cards (expandable)
        main_container.grid_rowconfigure(3, weight=0)  # Checkbox
        main_container.grid_rowconfigure(4, weight=0)  # Buttons
        main_container.grid_columnconfigure(0, weight=1)

        # --- Header Row ---
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        header_frame.grid_columnconfigure(0, weight=1)

        # Title (centered)
        title_label = ctk.CTkLabel(
            header_frame,
            text=self.translator.get("selection_title", default="Choose Your Installation"),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=FLY_AGARIC_WHITE
        )
        title_label.grid(row=0, column=0)

        # Language selector (right side)
        lang_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        lang_frame.grid(row=0, column=1, sticky="e", padx=(10, 0))

        lang_label = ctk.CTkLabel(
            lang_frame,
            text=self.translator.get("language_switcher_label", default="Language:"),
            font=ctk.CTkFont(size=10),
            text_color="gray70"
        )
        lang_label.pack(side="left", padx=(0, 5))

        self.language_option_menu = ctk.CTkOptionMenu(
            lang_frame,
            values=["en", "ru"],
            command=self._on_language_select,
            fg_color=FLY_AGARIC_RED,
            button_color=FLY_AGARIC_RED,
            button_hover_color=FLY_AGARIC_WHITE,
            width=65,
            height=26,
            font=ctk.CTkFont(size=11)
        )
        self.language_option_menu.set(self.translator.current_lang)
        self.language_option_menu.pack(side="left")

        # --- Subtitle ---
        subtitle_label = ctk.CTkLabel(
            main_container,
            text=self.translator.get(
                "selection_subtitle",
                default="Select which component you want to install or launch"
            ),
            font=ctk.CTkFont(size=12),
            text_color=FLY_AGARIC_WHITE
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 15))

        # --- Cards Container ---
        cards_container = ctk.CTkFrame(main_container, fg_color="transparent")
        cards_container.grid(row=2, column=0, sticky="nsew", padx=15, pady=10)

        # Configure cards grid - equal width columns
        cards_container.grid_rowconfigure(0, weight=1)
        cards_container.grid_columnconfigure(0, weight=1, minsize=300)
        cards_container.grid_columnconfigure(1, weight=1, minsize=300)

        # --- GAMMA Card ---
        gamma_card = ctk.CTkFrame(
            cards_container,
            fg_color=FLY_AGARIC_BLACK,
            border_color=GAMMA_BLUE,
            border_width=3,
            corner_radius=10
        )
        gamma_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        # GAMMA content
        gamma_content = ctk.CTkFrame(gamma_card, fg_color="transparent")
        gamma_content.pack(expand=True, fill="both", padx=15, pady=15)

        gamma_logo_label = ctk.CTkLabel(
            gamma_content,
            text="🎮",
            font=ctk.CTkFont(size=48)
        )
        gamma_logo_label.pack(pady=(5, 8))

        gamma_title = ctk.CTkLabel(
            gamma_content,
            text=self.translator.get("gamma_title", default="STALKER GAMMA"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=GAMMA_BLUE
        )
        gamma_title.pack(pady=3)

        gamma_subtitle = ctk.CTkLabel(
            gamma_content,
            text=self.translator.get("gamma_subtitle", default="Modpack"),
            font=ctk.CTkFont(size=12),
            text_color=FLY_AGARIC_WHITE
        )
        gamma_subtitle.pack(pady=2)

        gamma_description = ctk.CTkLabel(
            gamma_content,
            text=self.translator.get(
                "gamma_description_short",
                default="Complete GAMMA modpack\nwith 150+ mods"
            ),
            font=ctk.CTkFont(size=11),
            text_color="gray80",
            justify="center"
        )
        gamma_description.pack(pady=8)

        # Button packed at bottom
        gamma_button = ctk.CTkButton(
            gamma_content,
            text=self.translator.get("gamma_install_button", default="Install GAMMA"),
            command=self._on_gamma_selected,
            fg_color=GAMMA_BLUE,
            hover_color=GAMMA_ORANGE,
            text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=8
        )
        gamma_button.pack(side="bottom", fill="x", pady=(10, 0))

        # --- AOEngine Card ---
        aoengine_card = ctk.CTkFrame(
            cards_container,
            fg_color=FLY_AGARIC_BLACK,
            border_color=FLY_AGARIC_RED,
            border_width=3,
            corner_radius=10
        )
        aoengine_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        # AOEngine content
        aoengine_content = ctk.CTkFrame(aoengine_card, fg_color="transparent")
        aoengine_content.pack(expand=True, fill="both", padx=15, pady=15)

        aoengine_logo_label = ctk.CTkLabel(
            aoengine_content,
            text="🍄",
            font=ctk.CTkFont(size=48)
        )
        aoengine_logo_label.pack(pady=(5, 8))

        aoengine_title = ctk.CTkLabel(
            aoengine_content,
            text=self.translator.get("aoengine_title", default="AOEngine"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=FLY_AGARIC_RED
        )
        aoengine_title.pack(pady=3)

        aoengine_subtitle = ctk.CTkLabel(
            aoengine_content,
            text=self.translator.get("aoengine_subtitle", default="Launcher"),
            font=ctk.CTkFont(size=12),
            text_color=FLY_AGARIC_WHITE
        )
        aoengine_subtitle.pack(pady=2)

        aoengine_description = ctk.CTkLabel(
            aoengine_content,
            text=self.translator.get(
                "aoengine_description_short",
                default="Manage AOEngine files\nwith auto-updates"
            ),
            font=ctk.CTkFont(size=11),
            text_color="gray80",
            justify="center"
        )
        aoengine_description.pack(pady=8)

        # Button packed at bottom
        aoengine_button = ctk.CTkButton(
            aoengine_content,
            text=self.translator.get("aoengine_launch_button", default="Launch AOEngine"),
            command=self._on_aoengine_selected,
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE,
            text_color=FLY_AGARIC_WHITE,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            corner_radius=8
        )
        aoengine_button.pack(side="bottom", fill="x", pady=(10, 0))

        # --- Sequential Checkbox ---
        sequential_checkbox = ctk.CTkCheckBox(
            main_container,
            text=self.translator.get(
                "sequential_mode_label",
                default="Install GAMMA first, then proceed to AOEngine"
            ),
            variable=self.sequential_mode,
            font=ctk.CTkFont(size=11),
            text_color=FLY_AGARIC_WHITE,
            fg_color=GAMMA_BLUE,
            hover_color=GAMMA_ORANGE,
            border_color=GAMMA_BLUE
        )
        sequential_checkbox.grid(row=3, column=0, pady=12)

        # --- Bottom Buttons ---
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.grid(row=4, column=0, pady=(0, 15), padx=15, sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        settings_button = ctk.CTkButton(
            button_frame,
            text=self.translator.get("settings_button", default="Settings"),
            command=self._open_settings,
            fg_color="transparent",
            border_color=FLY_AGARIC_RED,
            border_width=2,
            text_color=FLY_AGARIC_WHITE,
            hover_color=FLY_AGARIC_RED,
            width=90,
            height=32,
            font=ctk.CTkFont(size=11)
        )
        settings_button.grid(row=0, column=0, sticky="w", padx=3)

        about_button = ctk.CTkButton(
            button_frame,
            text=self.translator.get("about_button", default="About"),
            command=self._open_about,
            fg_color="transparent",
            border_color=FLY_AGARIC_RED,
            border_width=2,
            text_color=FLY_AGARIC_WHITE,
            hover_color=FLY_AGARIC_RED,
            width=90,
            height=32,
            font=ctk.CTkFont(size=11)
        )
        about_button.grid(row=0, column=1, padx=3)

        exit_button = ctk.CTkButton(
            button_frame,
            text=self.translator.get("exit_button", default="Exit"),
            command=self.quit,
            fg_color="transparent",
            border_color=FLY_AGARIC_RED,
            border_width=2,
            text_color=FLY_AGARIC_WHITE,
            hover_color=FLY_AGARIC_RED,
            width=90,
            height=32,
            font=ctk.CTkFont(size=11)
        )
        exit_button.grid(row=0, column=2, sticky="e", padx=3)

    def _on_gamma_selected(self):
        """Handle GAMMA installation selection."""
        logging.info("GAMMA installation selected")

        # Import here to avoid circular dependency
        from launcher.gui.gamma.gamma_window import GammaInstallerWindow

        # Hide selection window
        self.withdraw()

        # Handle sequential mode
        if self.sequential_mode.get():
            # Launch AOEngine after GAMMA completion
            gamma_window = GammaInstallerWindow(self, launch_aoengine_callback=self._launch_aoengine_after_gamma)
        else:
            # Just exit when GAMMA installation is done
            gamma_window = GammaInstallerWindow(self)

    def _launch_aoengine_after_gamma(self):
        """Launch AOEngine launcher after GAMMA installation completes."""
        logging.info("GAMMA installation complete, launching AOEngine...")

        # Show selection window briefly
        self.deiconify()

        # Launch AOEngine
        self._on_aoengine_selected()

    def _on_aoengine_selected(self):
        """Handle AOEngine launcher selection."""
        logging.info("AOEngine launcher selected")

        # Import here to avoid circular dependency
        from launcher.gui.main_window import App

        # Close selection window
        self.destroy()

        # Create and run AOEngine launcher
        app = App()
        app.mainloop()

    def _on_language_select(self, language: str):
        """Handle language selection."""
        self.translator.set_language(language)
        self.config_manager.update_config(language=language)

        # Refresh UI text
        self._refresh_ui_text()

    def _refresh_ui_text(self):
        """Refresh all UI text to current language."""
        messagebox.showinfo(
            self.translator.get("language_changed_title", default="Language Changed"),
            self.translator.get(
                "language_changed_message",
                default="Language has been changed. Please restart the application for full effect."
            )
        )

    def _open_settings(self):
        """Open settings dialog."""
        messagebox.showinfo(
            self.translator.get("settings_button", default="Settings"),
            "Settings dialog coming soon.\n\nFor now, use the individual launcher settings."
        )

    def _open_about(self):
        """Open about dialog."""
        from launcher.gui.main_window import InfoWindow

        about_window = InfoWindow(
            self,
            title=self.translator.get("about_window_title", default="About AOEngine Tools"),
            description=self.translator.get(
                "about_description",
                default="AOEngine Tools v2.0.0\nGAMMA Integration Edition\n\n"
                        "A unified launcher for S.T.A.L.K.E.R. Anomaly modding.\n\n"
                        "Components:\n"
                        "• GAMMA Installer - Install STALKER GAMMA modpack\n"
                        "• AOEngine Launcher - Manage AOEngine files\n"
                        "• Uploader Tool - Developer release management"
            )
        )
        about_window.grab_set()
