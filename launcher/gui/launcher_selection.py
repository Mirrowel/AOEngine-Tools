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
        self.resizable(False, False)  # Non-resizable, auto-sizes to content

        # Set up dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Config and translator
        self.config_manager = ConfigManager()
        self.translator = get_translator()

        # Store references to widgets that need text updates
        self.text_widgets = {}

        self._create_widgets()

    def _create_widgets(self):
        """Creates and lays out all GUI widgets - auto-sizing with pack."""
        # Main container - auto-sizes to content
        main_container = ctk.CTkFrame(
            self,
            fg_color=FLY_AGARIC_BLACK,
            border_color=FLY_AGARIC_RED,
            border_width=2
        )
        main_container.pack(padx=10, pady=10, fill="both", expand=True)

        # --- Header Row ---
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(10, 5))

        # Language selector (top right corner)
        lang_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        lang_frame.pack(side="right", anchor="ne")

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

        # Title (centered below language selector)
        title_label = ctk.CTkLabel(
            header_frame,
            text=self.translator.get("selection_title", default="Choose Your Installation"),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=FLY_AGARIC_WHITE
        )
        title_label.pack(pady=(5, 5))
        self.text_widgets['title'] = title_label

        # --- Subtitle ---
        subtitle_label = ctk.CTkLabel(
            main_container,
            text=self.translator.get(
                "selection_subtitle",
                default="Select which component you want to install or launch"
            ),
            font=ctk.CTkFont(size=11),
            text_color="gray70"
        )
        subtitle_label.pack(pady=(0, 10))
        self.text_widgets['subtitle'] = subtitle_label

        # --- Cards Container ---
        cards_container = ctk.CTkFrame(main_container, fg_color="transparent")
        cards_container.pack(fill="x", padx=15, pady=(0, 10))

        # --- GAMMA Card ---
        gamma_card = ctk.CTkFrame(
            cards_container,
            fg_color=FLY_AGARIC_BLACK,
            border_color=GAMMA_BLUE,
            border_width=3,
            corner_radius=10,
            width=340
        )
        gamma_card.pack(side="left", padx=(0, 8), fill="both", expand=True)
        gamma_card.pack_propagate(False)  # Maintain size

        # GAMMA content
        gamma_content = ctk.CTkFrame(gamma_card, fg_color="transparent")
        gamma_content.pack(fill="both", expand=True, padx=12, pady=10)

        gamma_logo_label = ctk.CTkLabel(
            gamma_content,
            text="🎮",
            font=ctk.CTkFont(size=40)
        )
        gamma_logo_label.pack(pady=(0, 5))

        gamma_title = ctk.CTkLabel(
            gamma_content,
            text=self.translator.get("gamma_title", default="STALKER GAMMA"),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=GAMMA_BLUE
        )
        gamma_title.pack(pady=2)
        self.text_widgets['gamma_title'] = gamma_title

        gamma_description = ctk.CTkLabel(
            gamma_content,
            text=self.translator.get(
                "gamma_description_short",
                default="Complete GAMMA modpack\nwith 150+ mods"
            ),
            font=ctk.CTkFont(size=12),
            text_color="gray80",
            justify="center"
        )
        gamma_description.pack(pady=5)
        self.text_widgets['gamma_description'] = gamma_description

        # View Details button
        gamma_details_button = ctk.CTkButton(
            gamma_content,
            text=self.translator.get("view_details_button", default="View Details"),
            command=lambda: self._show_details("gamma"),
            fg_color="transparent",
            border_color=GAMMA_BLUE,
            border_width=1,
            text_color=GAMMA_BLUE,
            hover_color=GAMMA_BLUE,
            height=28,
            font=ctk.CTkFont(size=10)
        )
        gamma_details_button.pack(pady=(5, 10), padx=20, fill="x")
        self.text_widgets['gamma_details_button'] = gamma_details_button

        # Install button
        gamma_button = ctk.CTkButton(
            gamma_content,
            text=self.translator.get("gamma_install_button", default="Install GAMMA"),
            command=self._on_gamma_selected,
            fg_color=GAMMA_BLUE,
            hover_color=GAMMA_ORANGE,
            text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=35,
            corner_radius=8
        )
        gamma_button.pack(side="bottom", pady=(0, 5), padx=8, fill="x")
        self.text_widgets['gamma_button'] = gamma_button

        # --- AOEngine Card ---
        aoengine_card = ctk.CTkFrame(
            cards_container,
            fg_color=FLY_AGARIC_BLACK,
            border_color=FLY_AGARIC_RED,
            border_width=3,
            corner_radius=10,
            width=340
        )
        aoengine_card.pack(side="left", padx=(8, 0), fill="both", expand=True)
        aoengine_card.pack_propagate(False)  # Maintain size

        # AOEngine content
        aoengine_content = ctk.CTkFrame(aoengine_card, fg_color="transparent")
        aoengine_content.pack(fill="both", expand=True, padx=12, pady=10)

        aoengine_logo_label = ctk.CTkLabel(
            aoengine_content,
            text="🍄",
            font=ctk.CTkFont(size=40)
        )
        aoengine_logo_label.pack(pady=(0, 5))

        aoengine_title = ctk.CTkLabel(
            aoengine_content,
            text=self.translator.get("aoengine_title", default="AOEngine"),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=FLY_AGARIC_RED
        )
        aoengine_title.pack(pady=2)
        self.text_widgets['aoengine_title'] = aoengine_title

        aoengine_description = ctk.CTkLabel(
            aoengine_content,
            text=self.translator.get(
                "aoengine_description_short",
                default="Manage AOEngine files\nwith auto-updates"
            ),
            font=ctk.CTkFont(size=12),
            text_color="gray80",
            justify="center"
        )
        aoengine_description.pack(pady=5)
        self.text_widgets['aoengine_description'] = aoengine_description

        # View Details button
        aoengine_details_button = ctk.CTkButton(
            aoengine_content,
            text=self.translator.get("view_details_button", default="View Details"),
            command=lambda: self._show_details("aoengine"),
            fg_color="transparent",
            border_color=FLY_AGARIC_RED,
            border_width=1,
            text_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_RED,
            height=28,
            font=ctk.CTkFont(size=10)
        )
        aoengine_details_button.pack(pady=(5, 10), padx=20, fill="x")
        self.text_widgets['aoengine_details_button'] = aoengine_details_button

        # Launch button
        aoengine_button = ctk.CTkButton(
            aoengine_content,
            text=self.translator.get("aoengine_launch_button", default="Launch AOEngine"),
            command=self._on_aoengine_selected,
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE,
            text_color=FLY_AGARIC_WHITE,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=35,
            corner_radius=8
        )
        aoengine_button.pack(side="bottom", pady=(0, 5), padx=8, fill="x")
        self.text_widgets['aoengine_button'] = aoengine_button

        # --- Bottom Buttons ---
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(5, 10), padx=15)

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
            height=30,
            font=ctk.CTkFont(size=10)
        )
        settings_button.pack(side="left", padx=3)
        self.text_widgets['settings_button'] = settings_button

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
            height=30,
            font=ctk.CTkFont(size=10)
        )
        about_button.pack(side="left", padx=3)
        self.text_widgets['about_button'] = about_button

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
            height=30,
            font=ctk.CTkFont(size=10)
        )
        exit_button.pack(side="right", padx=3)
        self.text_widgets['exit_button'] = exit_button

    def _on_gamma_selected(self):
        """Handle GAMMA installation selection."""
        logging.info("GAMMA installation selected")

        # Import here to avoid circular dependency
        from launcher.gui.gamma.gamma_window import GammaInstallerWindow

        # Hide selection window
        self.withdraw()

        # Create GAMMA installer (it will ask user to launch AOEngine after install if desired)
        gamma_window = GammaInstallerWindow(self)

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

    def _show_details(self, component: str):
        """Show full description dialog for a component."""
        if component == "gamma":
            title = self.translator.get("gamma_title", default="STALKER GAMMA")
            description = self.translator.get(
                "gamma_description",
                default="Install the complete GAMMA\nmodpack for S.T.A.L.K.E.R.\nAnomaly with 150+ mods\nand ModOrganizer2"
            )
        else:  # aoengine
            title = self.translator.get("aoengine_title", default="AOEngine")
            description = self.translator.get(
                "aoengine_description",
                default="Install and manage AOEngine\nfiles for S.T.A.L.K.E.R.\nAnomaly with automatic\nversion management"
            )

        messagebox.showinfo(title, description)

    def _on_language_select(self, language: str):
        """Handle language selection."""
        self.translator.set_language(language)
        self.config_manager.update_config(language=language)

        # Refresh UI text
        self._refresh_ui_text()

    def _refresh_ui_text(self):
        """Refresh all UI text to current language."""
        # Update all text widgets with new language
        self.text_widgets['title'].configure(
            text=self.translator.get("selection_title", default="Choose Your Installation")
        )
        self.text_widgets['subtitle'].configure(
            text=self.translator.get(
                "selection_subtitle",
                default="Select which component you want to install or launch"
            )
        )

        # GAMMA card
        self.text_widgets['gamma_title'].configure(
            text=self.translator.get("gamma_title", default="STALKER GAMMA")
        )
        self.text_widgets['gamma_description'].configure(
            text=self.translator.get(
                "gamma_description_short",
                default="Complete GAMMA modpack\nwith 150+ mods"
            )
        )
        self.text_widgets['gamma_details_button'].configure(
            text=self.translator.get("view_details_button", default="View Details")
        )
        self.text_widgets['gamma_button'].configure(
            text=self.translator.get("gamma_install_button", default="Install GAMMA")
        )

        # AOEngine card
        self.text_widgets['aoengine_title'].configure(
            text=self.translator.get("aoengine_title", default="AOEngine")
        )
        self.text_widgets['aoengine_description'].configure(
            text=self.translator.get(
                "aoengine_description_short",
                default="Manage AOEngine files\nwith auto-updates"
            )
        )
        self.text_widgets['aoengine_details_button'].configure(
            text=self.translator.get("view_details_button", default="View Details")
        )
        self.text_widgets['aoengine_button'].configure(
            text=self.translator.get("aoengine_launch_button", default="Launch AOEngine")
        )

        # Bottom buttons
        self.text_widgets['settings_button'].configure(
            text=self.translator.get("settings_button", default="Settings")
        )
        self.text_widgets['about_button'].configure(
            text=self.translator.get("about_button", default="About")
        )
        self.text_widgets['exit_button'].configure(
            text=self.translator.get("exit_button", default="Exit")
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
