"""
GAMMA Installer GUI Window - Professional Redesign

Modern tabbed interface for GAMMA modpack installation with:
- Main installation tab
- Mods list viewer
- Update detection
- Backup management
- Compact, professional layout
"""

import customtkinter as ctk
import threading
import queue
import logging
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

from launcher.core.gamma import (
    GammaInstaller,
    GammaConfig,
    InstallationState,
    InstallationPhase
)
from shared.localization import get_translator

logger = logging.getLogger(__name__)

# GAMMA theme colors
GAMMA_PRIMARY = "#00A8E8"  # Bright blue
GAMMA_SECONDARY = "#FF6B35"  # Orange accent
GAMMA_SUCCESS = "#4CAF50"
GAMMA_WARNING = "#FF9800"
GAMMA_ERROR = "#F44336"
GAMMA_BG = "#1a1a1a"
GAMMA_FG = "#2d2d2d"


class GammaInstallerWindow(ctk.CTkToplevel):
    """
    Professional GAMMA Installer window with tabbed interface.

    Features:
    - Tabbed interface (Main, Mods List, Updates, Backup)
    - Compact sidebar with controls
    - Separate console log window
    - Update detection and mod status
    - Professional, clean layout
    """

    def __init__(self, parent, launch_aoengine_callback: Optional[callable] = None):
        """
        Initialize GAMMA installer window.

        Args:
            parent: Parent window
            launch_aoengine_callback: Callback to launch AOEngine after completion
        """
        super().__init__(parent)

        self.title("STALKER GAMMA Launcher - Mirrowel's AOEngine Tools")
        self.geometry("950x600")
        self.resizable(True, True)

        self.launch_aoengine_callback = launch_aoengine_callback
        self.translator = get_translator()

        # Configuration
        self.config = GammaConfig(
            anomaly_path=Path.home() / "Games" / "Anomaly",
            gamma_path=Path.home() / "Games" / ".Grok's Modpack Installer" / "G.A.M.M.A",
            cache_path=Path.home() / ".cache" / "gamma_launcher"
        )

        # Installer instance
        self.installer: Optional[GammaInstaller] = None
        self.installation_thread: Optional[threading.Thread] = None

        # GUI update queue
        self.gui_queue = queue.Queue()

        # Console window reference
        self.console_window: Optional[ConsoleLogWindow] = None

        # Create UI
        self._create_widgets()

        # Start queue processing
        self.after(100, self._process_gui_queue)

        # Make modal
        self.transient(parent)
        self.grab_set()

    def _create_widgets(self):
        """Create all GUI widgets with tabbed layout."""

        # Main container
        container = ctk.CTkFrame(self, fg_color=GAMMA_BG)
        container.pack(fill="both", expand=True)

        # Configure grid
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # --- Left Sidebar ---
        self._create_sidebar(container)

        # --- Right Content Area (Tabbed) ---
        self._create_tabs(container)

        # --- Bottom Progress Bar ---
        self._create_progress_bar(container)

    def _create_sidebar(self, parent):
        """Create left sidebar with controls and options."""
        sidebar = ctk.CTkFrame(parent, fg_color=GAMMA_FG, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)

        # Logo/Version section
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(pady=15, padx=10, fill="x")

        logo_label = ctk.CTkLabel(
            logo_frame,
            text="GAMMA",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=GAMMA_PRIMARY
        )
        logo_label.pack()

        version_label = ctk.CTkLabel(
            logo_frame,
            text="v0.22.0.0",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        version_label.pack()

        # Separator
        separator1 = ctk.CTkFrame(sidebar, fg_color="gray30", height=2)
        separator1.pack(fill="x", padx=10, pady=10)

        # Utility buttons
        utility_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        utility_frame.pack(pady=5, padx=10, fill="x")

        downgrade_btn = ctk.CTkButton(
            utility_frame,
            text="Downgrade ModOrganizer",
            fg_color="transparent",
            border_width=1,
            border_color="gray50",
            text_color="white",
            hover_color="gray30",
            height=30,
            font=ctk.CTkFont(size=11)
        )
        downgrade_btn.pack(fill="x", pady=3)

        first_install_btn = ctk.CTkButton(
            utility_frame,
            text="First Install Initialization",
            fg_color="transparent",
            border_width=1,
            border_color="gray50",
            text_color="white",
            hover_color="gray30",
            height=30,
            font=ctk.CTkFont(size=11),
            command=self._on_first_install
        )
        first_install_btn.pack(fill="x", pady=3)

        defender_btn = ctk.CTkButton(
            utility_frame,
            text="Add Defender Exclusions",
            fg_color="transparent",
            border_width=1,
            border_color="gray50",
            text_color="white",
            hover_color="gray30",
            height=30,
            font=ctk.CTkFont(size=11)
        )
        defender_btn.pack(fill="x", pady=3)

        longpaths_btn = ctk.CTkButton(
            utility_frame,
            text="Enable Long Paths",
            fg_color="transparent",
            border_width=1,
            border_color="gray50",
            text_color="white",
            hover_color="gray30",
            height=30,
            font=ctk.CTkFont(size=11)
        )
        longpaths_btn.pack(fill="x", pady=3)

        # Separator
        separator2 = ctk.CTkFrame(sidebar, fg_color="gray30", height=2)
        separator2.pack(fill="x", padx=10, pady=10)

        # Main Install/Update button (large, highlighted)
        self.install_button = ctk.CTkButton(
            sidebar,
            text="Install / Update\nGAMMA",
            fg_color=GAMMA_PRIMARY,
            hover_color=GAMMA_SECONDARY,
            text_color="white",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=60,
            corner_radius=8,
            command=self._on_install_clicked
        )
        self.install_button.pack(pady=10, padx=10, fill="x")

        # Options checkboxes
        options_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        options_frame.pack(pady=5, padx=15, fill="x")

        self.check_md5_var = ctk.BooleanVar(value=True)
        check_md5_cb = ctk.CTkCheckBox(
            options_frame,
            text="Check MD5",
            variable=self.check_md5_var,
            font=ctk.CTkFont(size=11),
            fg_color=GAMMA_PRIMARY,
            hover_color=GAMMA_SECONDARY
        )
        check_md5_cb.pack(anchor="w", pady=2)

        self.force_git_var = ctk.BooleanVar(value=True)
        force_git_cb = ctk.CTkCheckBox(
            options_frame,
            text="Force git download",
            variable=self.force_git_var,
            font=ctk.CTkFont(size=11),
            fg_color=GAMMA_PRIMARY,
            hover_color=GAMMA_SECONDARY
        )
        force_git_cb.pack(anchor="w", pady=2)

        self.force_zip_var = ctk.BooleanVar(value=False)
        force_zip_cb = ctk.CTkCheckBox(
            options_frame,
            text="Force zip extraction",
            variable=self.force_zip_var,
            font=ctk.CTkFont(size=11),
            fg_color=GAMMA_PRIMARY,
            hover_color=GAMMA_SECONDARY
        )
        force_zip_cb.pack(anchor="w", pady=2)

        self.delete_reshade_var = ctk.BooleanVar(value=True)
        delete_reshade_cb = ctk.CTkCheckBox(
            options_frame,
            text="Delete ReShade DLLs",
            variable=self.delete_reshade_var,
            font=ctk.CTkFont(size=11),
            fg_color=GAMMA_PRIMARY,
            hover_color=GAMMA_SECONDARY
        )
        delete_reshade_cb.pack(anchor="w", pady=2)

        self.preserve_ltx_var = ctk.BooleanVar(value=False)
        preserve_ltx_cb = ctk.CTkCheckBox(
            options_frame,
            text="Preserve user.ltx",
            variable=self.preserve_ltx_var,
            font=ctk.CTkFont(size=11),
            fg_color=GAMMA_PRIMARY,
            hover_color=GAMMA_SECONDARY
        )
        preserve_ltx_cb.pack(anchor="w", pady=2)

        # Spacer to push bottom buttons down
        spacer = ctk.CTkFrame(sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Play button
        play_button = ctk.CTkButton(
            sidebar,
            text="Play",
            fg_color=GAMMA_SUCCESS,
            hover_color="#45a049",
            text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=8
        )
        play_button.pack(pady=10, padx=10, fill="x")

        # Console Log button
        console_button = ctk.CTkButton(
            sidebar,
            text="Console Log",
            fg_color="transparent",
            border_width=1,
            border_color=GAMMA_PRIMARY,
            text_color=GAMMA_PRIMARY,
            hover_color="gray30",
            height=32,
            font=ctk.CTkFont(size=11),
            command=self._open_console_log
        )
        console_button.pack(pady=5, padx=10, fill="x")

        # Settings button
        settings_button = ctk.CTkButton(
            sidebar,
            text="Settings",
            fg_color="transparent",
            border_width=1,
            border_color="gray50",
            text_color="white",
            hover_color="gray30",
            height=32,
            font=ctk.CTkFont(size=11),
            command=self._open_settings
        )
        settings_button.pack(pady=5, padx=10, fill="x")

    def _create_tabs(self, parent):
        """Create right content area with tabs."""
        # Tabview
        self.tabview = ctk.CTkTabview(parent, fg_color=GAMMA_BG, segmented_button_fg_color=GAMMA_FG)
        self.tabview.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        # Add tabs
        self.tabview.add("Main")
        self.tabview.add("Mods List")
        self.tabview.add("GAMMA Updates")
        self.tabview.add("ModDB Updates")
        self.tabview.add("Backup")

        # Configure Main tab
        self._create_main_tab()

        # Configure Mods List tab
        self._create_mods_list_tab()

        # Configure GAMMA Updates tab
        self._create_gamma_updates_tab()

        # Configure ModDB Updates tab
        self._create_moddb_updates_tab()

        # Configure Backup tab
        self._create_backup_tab()

    def _create_main_tab(self):
        """Create main installation tab content."""
        main_tab = self.tabview.tab("Main")

        # Info text area
        info_frame = ctk.CTkFrame(main_tab, fg_color=GAMMA_FG)
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header with update status
        header_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)

        self.gamma_update_label = ctk.CTkLabel(
            header_frame,
            text="G.A.M.M.A. addons update available: False",
            font=ctk.CTkFont(size=11),
            text_color="white",
            anchor="w"
        )
        self.gamma_update_label.pack(side="left", padx=5)

        self.moddb_update_label = ctk.CTkLabel(
            header_frame,
            text="ModDB addons update available: False",
            font=ctk.CTkFont(size=11),
            text_color="white",
            anchor="w"
        )
        self.moddb_update_label.pack(side="left", padx=20)

        # Word wrap toggle
        self.word_wrap_var = ctk.BooleanVar(value=True)
        word_wrap_cb = ctk.CTkCheckBox(
            header_frame,
            text="Word Wrap",
            variable=self.word_wrap_var,
            font=ctk.CTkFont(size=10),
            fg_color=GAMMA_PRIMARY
        )
        word_wrap_cb.pack(side="right", padx=5)

        # Main info textbox
        self.info_textbox = ctk.CTkTextbox(
            info_frame,
            fg_color=GAMMA_BG,
            text_color=GAMMA_SUCCESS,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.info_textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Insert welcome message
        welcome_text = """Welcome to the Gigantic Automated Modular Modpack for Anomaly installer

Be sure to check out the discord #how-to-install channel for full instructions:
https://www.discord.gg/stalker-gamma

Untick Check MD5 ONLY if your pack is already working and you want to update it.

Check the update status above and click Install/Update GAMMA if needed.

Currently working from the directory:
""" + str(self.config.gamma_path or "Not set")

        self.info_textbox.insert("1.0", welcome_text)
        self.info_textbox.configure(state="disabled")

        # Paths section (compact)
        paths_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        paths_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Anomaly path
        anomaly_label = ctk.CTkLabel(
            paths_frame,
            text="Anomaly:",
            font=ctk.CTkFont(size=11),
            width=80,
            anchor="w"
        )
        anomaly_label.grid(row=0, column=0, sticky="w", pady=3, padx=(0, 5))

        self.anomaly_entry = ctk.CTkEntry(
            paths_frame,
            placeholder_text="Anomaly path...",
            fg_color=GAMMA_BG,
            font=ctk.CTkFont(size=10)
        )
        self.anomaly_entry.grid(row=0, column=1, sticky="ew", pady=3, padx=5)
        self.anomaly_entry.insert(0, str(self.config.anomaly_path))

        anomaly_browse_btn = ctk.CTkButton(
            paths_frame,
            text="Browse...",
            width=80,
            height=28,
            fg_color=GAMMA_PRIMARY,
            hover_color=GAMMA_SECONDARY,
            font=ctk.CTkFont(size=10),
            command=lambda: self._browse_path("anomaly")
        )
        anomaly_browse_btn.grid(row=0, column=2, sticky="e", pady=3)

        # GAMMA path
        gamma_label = ctk.CTkLabel(
            paths_frame,
            text="GAMMA:",
            font=ctk.CTkFont(size=11),
            width=80,
            anchor="w"
        )
        gamma_label.grid(row=1, column=0, sticky="w", pady=3, padx=(0, 5))

        self.gamma_entry = ctk.CTkEntry(
            paths_frame,
            placeholder_text="GAMMA path...",
            fg_color=GAMMA_BG,
            font=ctk.CTkFont(size=10)
        )
        self.gamma_entry.grid(row=1, column=1, sticky="ew", pady=3, padx=5)
        self.gamma_entry.insert(0, str(self.config.gamma_path))

        gamma_browse_btn = ctk.CTkButton(
            paths_frame,
            text="Browse...",
            width=80,
            height=28,
            fg_color=GAMMA_PRIMARY,
            hover_color=GAMMA_SECONDARY,
            font=ctk.CTkFont(size=10),
            command=lambda: self._browse_path("gamma")
        )
        gamma_browse_btn.grid(row=1, column=2, sticky="e", pady=3)

        # Cache path
        cache_label = ctk.CTkLabel(
            paths_frame,
            text="Cache:",
            font=ctk.CTkFont(size=11),
            width=80,
            anchor="w"
        )
        cache_label.grid(row=2, column=0, sticky="w", pady=3, padx=(0, 5))

        self.cache_entry = ctk.CTkEntry(
            paths_frame,
            placeholder_text="Cache path...",
            fg_color=GAMMA_BG,
            font=ctk.CTkFont(size=10)
        )
        self.cache_entry.grid(row=2, column=1, sticky="ew", pady=3, padx=5)
        self.cache_entry.insert(0, str(self.config.cache_path))

        cache_browse_btn = ctk.CTkButton(
            paths_frame,
            text="Browse...",
            width=80,
            height=28,
            fg_color=GAMMA_PRIMARY,
            hover_color=GAMMA_SECONDARY,
            font=ctk.CTkFont(size=10),
            command=lambda: self._browse_path("cache")
        )
        cache_browse_btn.grid(row=2, column=2, sticky="e", pady=3)

        paths_frame.grid_columnconfigure(1, weight=1)

    def _create_mods_list_tab(self):
        """Create mods list tab showing all mods with status."""
        mods_tab = self.tabview.tab("Mods List")

        # Header
        header = ctk.CTkLabel(
            mods_tab,
            text="Installed Mods (Coming Soon)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=GAMMA_PRIMARY
        )
        header.pack(pady=10)

        # Mods list (scrollable frame)
        mods_scroll = ctk.CTkScrollableFrame(mods_tab, fg_color=GAMMA_FG)
        mods_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Placeholder
        placeholder = ctk.CTkLabel(
            mods_scroll,
            text="Mod list will be displayed here after installation.\n\n"
                 "Features:\n"
                 "• View all installed mods\n"
                 "• Check mod status (enabled/disabled)\n"
                 "• See mod versions\n"
                 "• Enable/disable individual mods",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left"
        )
        placeholder.pack(pady=50)

    def _create_gamma_updates_tab(self):
        """Create GAMMA updates tab for update detection."""
        updates_tab = self.tabview.tab("GAMMA Updates")

        # Header
        header = ctk.CTkLabel(
            updates_tab,
            text="GAMMA Definition Updates (Coming Soon)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=GAMMA_PRIMARY
        )
        header.pack(pady=10)

        # Content
        content_frame = ctk.CTkFrame(updates_tab, fg_color=GAMMA_FG)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Placeholder
        placeholder = ctk.CTkLabel(
            content_frame,
            text="GAMMA update detection will be shown here.\n\n"
                 "Features:\n"
                 "• Check for new GAMMA releases\n"
                 "• View changelog\n"
                 "• One-click update\n"
                 "• Version comparison",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left"
        )
        placeholder.pack(pady=50)

    def _create_moddb_updates_tab(self):
        """Create ModDB updates tab for individual mod updates."""
        moddb_tab = self.tabview.tab("ModDB Updates")

        # Header
        header = ctk.CTkLabel(
            moddb_tab,
            text="ModDB Addon Updates (Coming Soon)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=GAMMA_PRIMARY
        )
        header.pack(pady=10)

        # Content
        content_frame = ctk.CTkFrame(moddb_tab, fg_color=GAMMA_FG)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Placeholder
        placeholder = ctk.CTkLabel(
            content_frame,
            text="Individual mod update detection will be shown here.\n\n"
                 "Features:\n"
                 "• Check each mod for updates on ModDB\n"
                 "• Update individual mods\n"
                 "• Batch update all outdated mods\n"
                 "• View mod descriptions and changelogs",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left"
        )
        placeholder.pack(pady=50)

    def _create_backup_tab(self):
        """Create backup management tab."""
        backup_tab = self.tabview.tab("Backup")

        # Header
        header = ctk.CTkLabel(
            backup_tab,
            text="Backup Management (Coming Soon)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=GAMMA_PRIMARY
        )
        header.pack(pady=10)

        # Content
        content_frame = ctk.CTkFrame(backup_tab, fg_color=GAMMA_FG)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Placeholder
        placeholder = ctk.CTkLabel(
            content_frame,
            text="Backup management will be available here.\n\n"
                 "Features:\n"
                 "• Create backups before updates\n"
                 "• Restore previous installations\n"
                 "• Manage backup storage\n"
                 "• Backup compression",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            justify="left"
        )
        placeholder.pack(pady=50)

    def _create_progress_bar(self, parent):
        """Create bottom progress bar."""
        progress_frame = ctk.CTkFrame(parent, fg_color=GAMMA_FG, height=60)
        progress_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        progress_frame.grid_propagate(False)

        # Status label
        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color="white",
            anchor="w"
        )
        self.status_label.pack(side="left", padx=15, pady=(5, 0), anchor="w")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            progress_color=GAMMA_PRIMARY,
            height=20
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 15), pady=10)
        self.progress_bar.set(0)

        # Percentage label
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=ctk.CTkFont(size=11),
            text_color="white",
            width=50
        )
        self.progress_label.pack(side="right", padx=15)

    def _process_gui_queue(self):
        """Process GUI update queue."""
        try:
            while not self.gui_queue.empty():
                callback, args, kwargs = self.gui_queue.get_nowait()
                callback(*args, **kwargs)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_gui_queue)

    def _queue_gui_update(self, callback, *args, **kwargs):
        """Queue a GUI update from another thread."""
        self.gui_queue.put((callback, args, kwargs))

    def _on_install_clicked(self):
        """Handle install/update button click."""
        logging.info("Install/Update GAMMA clicked")
        # TODO: Implement actual installation logic
        messagebox.showinfo("Info", "Installation will be implemented soon.\n\nThis button will trigger the full GAMMA installation process.")

    def _on_first_install(self):
        """Handle first install initialization."""
        messagebox.showinfo("Info", "First install initialization will configure your system for GAMMA.")

    def _open_console_log(self):
        """Open console log window."""
        if self.console_window is None or not self.console_window.winfo_exists():
            self.console_window = ConsoleLogWindow(self)
        else:
            self.console_window.focus()

    def _open_settings(self):
        """Open settings dialog."""
        messagebox.showinfo("Settings", "Settings dialog coming soon.\n\nConfigure:\n• Download threads\n• Timeout values\n• Update check frequency")

    def _browse_path(self, path_type: str):
        """Browse for directory path."""
        title_map = {
            "anomaly": "Select Anomaly Directory",
            "gamma": "Select GAMMA Directory",
            "cache": "Select Cache Directory"
        }

        path = filedialog.askdirectory(title=title_map.get(path_type, "Select Directory"))
        if path:
            if path_type == "anomaly":
                self.anomaly_entry.delete(0, "end")
                self.anomaly_entry.insert(0, path)
                self.config.anomaly_path = Path(path)
            elif path_type == "gamma":
                self.gamma_entry.delete(0, "end")
                self.gamma_entry.insert(0, path)
                self.config.gamma_path = Path(path)
            elif path_type == "cache":
                self.cache_entry.delete(0, "end")
                self.cache_entry.insert(0, path)
                self.config.cache_path = Path(path)


class ConsoleLogWindow(ctk.CTkToplevel):
    """Separate window for console log output."""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("GAMMA Installer - Console Log")
        self.geometry("900x500")

        # Main frame
        main_frame = ctk.CTkFrame(self, fg_color=GAMMA_BG)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Header with clear button
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=5)

        title_label = ctk.CTkLabel(
            header_frame,
            text="Installation Log",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=GAMMA_PRIMARY
        )
        title_label.pack(side="left")

        clear_button = ctk.CTkButton(
            header_frame,
            text="Clear",
            width=80,
            height=28,
            fg_color=GAMMA_PRIMARY,
            hover_color=GAMMA_SECONDARY,
            command=self._clear_log
        )
        clear_button.pack(side="right")

        # Log textbox
        self.log_textbox = ctk.CTkTextbox(
            main_frame,
            fg_color=GAMMA_FG,
            text_color="white",
            font=ctk.CTkFont(family="Consolas", size=10),
            wrap="none"
        )
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _clear_log(self):
        """Clear the log."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

    def log(self, message: str):
        """Append message to log."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
