"""
GAMMA Installer GUI Window

Main window for GAMMA modpack installation with real-time progress tracking.
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


class GammaInstallerWindow(ctk.CTkToplevel):
    """
    GAMMA Installer window with real-time progress tracking.

    Features:
    - Phase and overall progress bars
    - Real-time console log
    - Path configuration (Anomaly, GAMMA, Cache)
    - Installation options (MD5 check, preserve user.ltx, etc.)
    - Start/Pause/Cancel controls
    - Automatic AOEngine launcher launch on completion (optional)
    """

    def __init__(self, parent, launch_aoengine_callback: Optional[callable] = None):
        """
        Initialize GAMMA installer window.

        Args:
            parent: Parent window
            launch_aoengine_callback: Callback to launch AOEngine after completion
        """
        super().__init__(parent)

        self.title("GAMMA Installer - Mirrowel's AOEngine Tools")
        self.geometry("900x700")

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

        # Create UI
        self._create_widgets()

        # Start queue processing
        self.after(100, self._process_gui_queue)

        # Make modal
        self.transient(parent)
        self.grab_set()

    def _create_widgets(self):
        """Create all GUI widgets."""

        # Main container with padding
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="S.T.A.L.K.E.R. GAMMA Installation",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=GAMMA_PRIMARY
        )
        title_label.pack(pady=(0, 10))

        # Progress section
        self._create_progress_section(main_frame)

        # Console log section
        self._create_console_section(main_frame)

        # Configuration section
        self._create_config_section(main_frame)

        # Options section
        self._create_options_section(main_frame)

        # Control buttons
        self._create_controls_section(main_frame)

    def _create_progress_section(self, parent):
        """Create progress display section."""

        progress_frame = ctk.CTkFrame(parent)
        progress_frame.pack(fill="x", pady=(0, 10))

        # Phase label
        self.phase_label = ctk.CTkLabel(
            progress_frame,
            text="Phase: Ready to install",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.phase_label.pack(pady=(10, 5))

        # Overall progress bar
        self.overall_progress = ctk.CTkProgressBar(
            progress_frame,
            width=850,
            height=25,
            mode="determinate"
        )
        self.overall_progress.pack(pady=5, padx=10)
        self.overall_progress.set(0)

        # Overall progress percentage
        self.overall_progress_label = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=ctk.CTkFont(size=12)
        )
        self.overall_progress_label.pack()

        # Current operation
        self.operation_label = ctk.CTkLabel(
            progress_frame,
            text="Current: Waiting to start...",
            font=ctk.CTkFont(size=12)
        )
        self.operation_label.pack(pady=(10, 5))

        # Current file progress
        self.file_progress = ctk.CTkProgressBar(
            progress_frame,
            width=850,
            height=15,
            mode="determinate"
        )
        self.file_progress.pack(pady=5, padx=10)
        self.file_progress.set(0)

        # Status label (time, mods count)
        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="Status: Ready",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(pady=(5, 10))

    def _create_console_section(self, parent):
        """Create console log section."""

        console_frame = ctk.CTkFrame(parent)
        console_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Console header
        console_header = ctk.CTkFrame(console_frame)
        console_header.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            console_header,
            text="Installation Log",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        clear_button = ctk.CTkButton(
            console_header,
            text="Clear",
            width=60,
            height=24,
            command=self._clear_console
        )
        clear_button.pack(side="right", padx=5)

        # Console text box
        self.console = ctk.CTkTextbox(
            console_frame,
            width=850,
            height=200,
            font=ctk.CTkFont(family="Courier", size=10)
        )
        self.console.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        self.console.configure(state="disabled")

    def _create_config_section(self, parent):
        """Create path configuration section."""

        config_frame = ctk.CTkFrame(parent)
        config_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            config_frame,
            text="Paths:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        # Anomaly path
        ctk.CTkLabel(config_frame, text="Anomaly:").grid(
            row=1, column=0, sticky="w", padx=10, pady=2
        )
        self.anomaly_path_entry = ctk.CTkEntry(config_frame, width=550)
        self.anomaly_path_entry.grid(row=1, column=1, padx=5, pady=2)
        self.anomaly_path_entry.insert(0, str(self.config.anomaly_path))

        ctk.CTkButton(
            config_frame,
            text="Browse...",
            width=80,
            command=lambda: self._browse_path(self.anomaly_path_entry)
        ).grid(row=1, column=2, padx=10, pady=2)

        # GAMMA path
        ctk.CTkLabel(config_frame, text="GAMMA:").grid(
            row=2, column=0, sticky="w", padx=10, pady=2
        )
        self.gamma_path_entry = ctk.CTkEntry(config_frame, width=550)
        self.gamma_path_entry.grid(row=2, column=1, padx=5, pady=2)
        self.gamma_path_entry.insert(0, str(self.config.gamma_path))

        ctk.CTkButton(
            config_frame,
            text="Browse...",
            width=80,
            command=lambda: self._browse_path(self.gamma_path_entry)
        ).grid(row=2, column=2, padx=10, pady=2)

        # Cache path
        ctk.CTkLabel(config_frame, text="Cache:").grid(
            row=3, column=0, sticky="w", padx=10, pady=2
        )
        self.cache_path_entry = ctk.CTkEntry(config_frame, width=550)
        self.cache_path_entry.grid(row=3, column=1, padx=5, pady=2)
        self.cache_path_entry.insert(0, str(self.config.cache_path))

        ctk.CTkButton(
            config_frame,
            text="Browse...",
            width=80,
            command=lambda: self._browse_path(self.cache_path_entry)
        ).grid(row=3, column=2, padx=10, pady=(2, 10))

    def _create_options_section(self, parent):
        """Create installation options section."""

        options_frame = ctk.CTkFrame(parent)
        options_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            options_frame,
            text="Options:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        # First row of checkboxes
        self.check_md5_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame,
            text="Verify MD5 hashes",
            variable=self.check_md5_var
        ).grid(row=1, column=0, sticky="w", padx=20, pady=2)

        self.force_git_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame,
            text="Force Git download",
            variable=self.force_git_var
        ).grid(row=1, column=1, sticky="w", padx=20, pady=2)

        # Second row of checkboxes
        self.preserve_ltx_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            options_frame,
            text="Preserve user.ltx",
            variable=self.preserve_ltx_var
        ).grid(row=2, column=0, sticky="w", padx=20, pady=2)

        self.delete_reshade_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame,
            text="Delete ReShade DLLs",
            variable=self.delete_reshade_var
        ).grid(row=2, column=1, sticky="w", padx=20, pady=(2, 10))

        # Launch AOEngine checkbox
        self.launch_aoengine_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            options_frame,
            text="Launch AOEngine Launcher after completion",
            variable=self.launch_aoengine_var,
            font=ctk.CTkFont(weight="bold")
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 10))

    def _create_controls_section(self, parent):
        """Create control buttons section."""

        controls_frame = ctk.CTkFrame(parent)
        controls_frame.pack(fill="x")

        button_frame = ctk.CTkFrame(controls_frame)
        button_frame.pack(pady=10)

        # Start button
        self.start_button = ctk.CTkButton(
            button_frame,
            text="Start Installation",
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=GAMMA_SUCCESS,
            hover_color="#45a049",
            command=self._start_installation
        )
        self.start_button.pack(side="left", padx=5)

        # Cancel button
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=120,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color=GAMMA_ERROR,
            hover_color="#da190b",
            command=self._cancel_installation,
            state="disabled"
        )
        self.cancel_button.pack(side="left", padx=5)

        # Close button
        self.close_button = ctk.CTkButton(
            button_frame,
            text="Close",
            width=120,
            height=40,
            font=ctk.CTkFont(size=14),
            command=self._close_window
        )
        self.close_button.pack(side="left", padx=5)

    def _browse_path(self, entry_widget):
        """Browse for directory path."""
        path = filedialog.askdirectory(title="Select Directory")
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)

    def _clear_console(self):
        """Clear console log."""
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")

    def _log_to_console(self, message: str, level: str = "INFO"):
        """Add message to console log."""
        self.console.configure(state="normal")

        # Color based on level
        color = {
            "INFO": "white",
            "SUCCESS": GAMMA_SUCCESS,
            "WARNING": GAMMA_WARNING,
            "ERROR": GAMMA_ERROR
        }.get(level, "white")

        self.console.insert("end", f"{message}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def _update_from_state(self, state: InstallationState):
        """Update GUI from installation state."""

        # Update phase
        phase_text = state.phase.value.replace("_", " ").title()
        self.phase_label.configure(text=f"Phase: {phase_text}")

        # Update overall progress
        self.overall_progress.set(state.overall_progress)
        self.overall_progress_label.configure(
            text=f"{int(state.overall_progress * 100)}%"
        )

        # Update operation
        self.operation_label.configure(text=f"Current: {state.current_operation}")

        # Update file progress
        if state.current_file_progress > 0:
            self.file_progress.set(state.current_file_progress)
        else:
            self.file_progress.set(0)

        # Update status
        elapsed_str = state.format_time(state.get_elapsed_time())
        remaining_str = state.format_time(state.get_estimated_time_remaining())

        status_parts = [f"Elapsed: {elapsed_str}"]

        if state.total_mods > 0:
            status_parts.append(
                f"Mods: {state.installed_mods}/{state.total_mods}"
            )

        if remaining_str != "Unknown":
            status_parts.append(f"Remaining: ~{remaining_str}")

        self.status_label.configure(text=" | ".join(status_parts))

        # Log errors and warnings
        for error in state.errors:
            if error:  # Avoid duplicate logs
                self._log_to_console(f"ERROR: {error}", "ERROR")
        state.errors.clear()

        for warning in state.warnings:
            if warning:
                self._log_to_console(f"WARNING: {warning}", "WARNING")
        state.warnings.clear()

        # Check completion
        if state.phase == InstallationPhase.COMPLETED:
            self._on_installation_complete()
        elif state.phase == InstallationPhase.FAILED:
            self._on_installation_failed()

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

    def _start_installation(self):
        """Start GAMMA installation."""

        # Update configuration from GUI
        self.config.anomaly_path = Path(self.anomaly_path_entry.get())
        self.config.gamma_path = Path(self.gamma_path_entry.get())
        self.config.cache_path = Path(self.cache_path_entry.get())
        self.config.check_md5 = self.check_md5_var.get()
        self.config.force_git_download = self.force_git_var.get()
        self.config.preserve_user_ltx = self.preserve_ltx_var.get()
        self.config.delete_reshade = self.delete_reshade_var.get()

        # Disable controls
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")

        # Clear console
        self._clear_console()
        self._log_to_console("Starting GAMMA installation...", "INFO")

        # Create installer
        self.installer = GammaInstaller(
            config=self.config,
            state_callback=lambda state: self._queue_gui_update(self._update_from_state, state)
        )

        # Start installation thread
        self.installation_thread = threading.Thread(
            target=self._run_installation,
            daemon=True
        )
        self.installation_thread.start()

    def _run_installation(self):
        """Run installation in background thread."""
        try:
            self.installer.install()
        except Exception as e:
            logger.exception("Installation error")
            self._queue_gui_update(
                self._log_to_console,
                f"Installation failed: {e}",
                "ERROR"
            )

    def _cancel_installation(self):
        """Cancel ongoing installation."""
        if messagebox.askyesno(
            "Cancel Installation",
            "Are you sure you want to cancel the installation?"
        ):
            self._log_to_console("Installation cancelled by user", "WARNING")
            # TODO: Implement cancellation logic
            self.cancel_button.configure(state="disabled")
            self.start_button.configure(state="normal")

    def _on_installation_complete(self):
        """Handle installation completion."""
        self._log_to_console("GAMMA installation completed successfully!", "SUCCESS")

        self.cancel_button.configure(state="disabled")
        self.start_button.configure(state="normal")

        # Show completion message
        result = messagebox.showinfo(
            "Installation Complete",
            "GAMMA has been installed successfully!\n\n"
            "You can now launch ModOrganizer2 from the GAMMA directory."
        )

        # Launch AOEngine if requested
        if self.launch_aoengine_var.get() and self.launch_aoengine_callback:
            self._log_to_console("Launching AOEngine Launcher...", "INFO")
            self.launch_aoengine_callback()
            self.destroy()

    def _on_installation_failed(self):
        """Handle installation failure."""
        self._log_to_console("GAMMA installation failed!", "ERROR")

        self.cancel_button.configure(state="disabled")
        self.start_button.configure(state="normal")

        messagebox.showerror(
            "Installation Failed",
            "GAMMA installation failed. Please check the log for details."
        )

    def _close_window(self):
        """Close the window."""
        if self.installation_thread and self.installation_thread.is_alive():
            if messagebox.askyesno(
                "Installation in Progress",
                "Installation is still running. Are you sure you want to close?"
            ):
                self.destroy()
        else:
            self.destroy()
