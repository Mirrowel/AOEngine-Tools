"""
Launcher Selection Screen

Provides the initial choice between GAMMA installation and AOEngine launcher.
Users can select which component to launch, with an option for sequential installation.
"""

import customtkinter as ctk
from tkinter import messagebox
import logging
from pathlib import Path

from shared.localization import get_translator

# Theme colors
FLY_AGARIC_RED = "#A52A2A"
FLY_AGARIC_WHITE = "#F9F6EE"
FLY_AGARIC_BLACK = "#2C1810"
GAMMA_BLUE = "#00A8E8"
GAMMA_ORANGE = "#FF6B35"


class LauncherSelectionWindow(ctk.CTk):
    """
    Initial launcher selection screen.

    Presents users with a choice between GAMMA modpack installation
    and AOEngine launcher, with an option for sequential installation.
    """

    def __init__(self):
        super().__init__()

        self.title("AOEngine Tools - Launcher Selection")
        self.geometry("700x450")
        self.resizable(True, True)

        # Set up dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Get translator
        self.translator = get_translator()

        # State
        self.sequential_mode = ctk.BooleanVar(value=False)

        self._create_widgets()

    def _create_widgets(self):
        """Creates and lays out all GUI widgets."""
        # Main container with minimal padding
        main_frame = ctk.CTkFrame(
            self,
            fg_color=FLY_AGARIC_BLACK,
            border_color=FLY_AGARIC_RED,
            border_width=2
        )
        main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text=self.translator.get("selection_title", default="Choose Your Installation"),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=FLY_AGARIC_WHITE
        )
        title_label.pack(pady=(15, 5))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text=self.translator.get(
                "selection_subtitle",
                default="Select which component you want to install or launch"
            ),
            font=ctk.CTkFont(size=12),
            text_color=FLY_AGARIC_WHITE
        )
        subtitle_label.pack(pady=(0, 15))

        # Cards container
        cards_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        cards_frame.pack(pady=5, padx=15, fill="both", expand=True)
        cards_frame.grid_columnconfigure((0, 1), weight=1)
        cards_frame.grid_rowconfigure(0, weight=1)

        # --- GAMMA Card ---
        gamma_card = ctk.CTkFrame(
            cards_frame,
            fg_color=FLY_AGARIC_BLACK,
            border_color=GAMMA_BLUE,
            border_width=3,
            corner_radius=10
        )
        gamma_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # GAMMA Logo placeholder (text for now)
        gamma_logo_label = ctk.CTkLabel(
            gamma_card,
            text="🎮",
            font=ctk.CTkFont(size=42)
        )
        gamma_logo_label.pack(pady=(15, 5))

        gamma_title = ctk.CTkLabel(
            gamma_card,
            text=self.translator.get("gamma_title", default="STALKER GAMMA"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=GAMMA_BLUE
        )
        gamma_title.pack(pady=3)

        gamma_subtitle = ctk.CTkLabel(
            gamma_card,
            text=self.translator.get("gamma_subtitle", default="Modpack"),
            font=ctk.CTkFont(size=12),
            text_color=FLY_AGARIC_WHITE
        )
        gamma_subtitle.pack(pady=2)

        gamma_description = ctk.CTkLabel(
            gamma_card,
            text=self.translator.get(
                "gamma_description",
                default="Install the complete GAMMA\nmodpack for S.T.A.L.K.E.R.\nAnomaly with 150+ mods\nand ModOrganizer2"
            ),
            font=ctk.CTkFont(size=11),
            text_color=FLY_AGARIC_WHITE,
            justify="center",
            wraplength=250
        )
        gamma_description.pack(pady=10, padx=15)

        gamma_button = ctk.CTkButton(
            gamma_card,
            text=self.translator.get("gamma_install_button", default="Install GAMMA"),
            command=self._on_gamma_selected,
            fg_color=GAMMA_BLUE,
            hover_color=GAMMA_ORANGE,
            text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            corner_radius=8
        )
        gamma_button.pack(pady=(5, 20), padx=15, fill="x")

        # --- AOEngine Card ---
        aoengine_card = ctk.CTkFrame(
            cards_frame,
            fg_color=FLY_AGARIC_BLACK,
            border_color=FLY_AGARIC_RED,
            border_width=3,
            corner_radius=10
        )
        aoengine_card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # AOEngine Logo placeholder (text for now)
        aoengine_logo_label = ctk.CTkLabel(
            aoengine_card,
            text="🍄",
            font=ctk.CTkFont(size=42)
        )
        aoengine_logo_label.pack(pady=(15, 5))

        aoengine_title = ctk.CTkLabel(
            aoengine_card,
            text=self.translator.get("aoengine_title", default="AOEngine"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=FLY_AGARIC_RED
        )
        aoengine_title.pack(pady=3)

        aoengine_subtitle = ctk.CTkLabel(
            aoengine_card,
            text=self.translator.get("aoengine_subtitle", default="Launcher"),
            font=ctk.CTkFont(size=12),
            text_color=FLY_AGARIC_WHITE
        )
        aoengine_subtitle.pack(pady=2)

        aoengine_description = ctk.CTkLabel(
            aoengine_card,
            text=self.translator.get(
                "aoengine_description",
                default="Install and manage AOEngine\nfiles for S.T.A.L.K.E.R.\nAnomaly with automatic\nversion management"
            ),
            font=ctk.CTkFont(size=11),
            text_color=FLY_AGARIC_WHITE,
            justify="center",
            wraplength=250
        )
        aoengine_description.pack(pady=10, padx=15)

        aoengine_button = ctk.CTkButton(
            aoengine_card,
            text=self.translator.get("aoengine_launch_button", default="Launch AOEngine"),
            command=self._on_aoengine_selected,
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE,
            text_color=FLY_AGARIC_WHITE,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            corner_radius=8
        )
        aoengine_button.pack(pady=(5, 20), padx=15, fill="x")

        # Sequential mode checkbox
        sequential_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        sequential_frame.pack(pady=8)

        sequential_checkbox = ctk.CTkCheckBox(
            sequential_frame,
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
        sequential_checkbox.pack()

        # Bottom button frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=8, padx=15, fill="x")
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
            height=32
        )
        settings_button.grid(row=0, column=0, sticky="w", padx=2)

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
            height=32
        )
        about_button.grid(row=0, column=1, padx=2)

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
            height=32
        )
        exit_button.grid(row=0, column=2, sticky="e", padx=2)

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

    def _open_settings(self):
        """Open settings dialog."""
        # TODO: Create a unified settings dialog
        messagebox.showinfo(
            "Settings",
            "Settings dialog coming soon.\n\n"
            "For now, use the individual launcher settings."
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
