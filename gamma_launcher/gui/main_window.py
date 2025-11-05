import customtkinter as ctk
import threading
from tkinter import filedialog, messagebox
import queue
import logging
from pathlib import Path
from typing import Optional

from gamma_launcher.core.config import GammaConfigManager
from gamma_launcher.core.models import InstallProgress
from gamma_launcher.core.workflow import GammaWorkflow
from gamma_launcher.utils.logging import log_queue, log_history
from shared.localization import init_translator, get_translator

FLY_AGARIC_RED = "#A52A2A"
FLY_AGARIC_WHITE = "#F9F6EE"
FLY_AGARIC_BLACK = "#2C1810"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GAMMA Launcher")
        self.geometry("800x600")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.config_manager = GammaConfigManager()
        self.translator = init_translator("gamma_launcher/locale", self.config_manager.get_config().language)

        self.gui_queue = queue.Queue()
        self.after(100, self._process_gui_queue)
        self.after(100, self._process_log_queue)

        self.install_ao_after = False
        self.console_window: Optional[ConsoleWindow] = None

        self._create_widgets()
        self._update_ui_text()
        self._load_paths_from_config()

    def _queue_ui_update(self, callback, *args, **kwargs):
        self.gui_queue.put((callback, args, kwargs))

    def _process_gui_queue(self):
        processed = 0
        max_per_call = 50
        try:
            while not self.gui_queue.empty() and processed < max_per_call:
                callback, args, kwargs = self.gui_queue.get_nowait()
                callback(*args, **kwargs)
                processed += 1
        except queue.Empty:
            pass
        finally:
            self.after(10, self._process_gui_queue)

    def _process_log_queue(self):
        try:
            while not log_queue.empty():
                message = log_queue.get_nowait()
                if self.console_window and self.console_window.winfo_exists():
                    self.console_window.log(message)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_log_queue)

    def _create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color=FLY_AGARIC_BLACK, border_color=FLY_AGARIC_RED, border_width=2)
        main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(5, weight=1)

        welcome_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        welcome_frame.grid(row=0, column=0, pady=10, padx=10, sticky="ew")

        self.welcome_label = ctk.CTkLabel(
            welcome_frame,
            text="",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=FLY_AGARIC_WHITE
        )
        self.welcome_label.pack()

        self.welcome_text = ctk.CTkTextbox(
            welcome_frame,
            height=100,
            fg_color=FLY_AGARIC_WHITE,
            text_color=FLY_AGARIC_BLACK,
            border_color=FLY_AGARIC_RED,
            border_width=2,
            wrap="word"
        )
        self.welcome_text.pack(fill="both", expand=True, pady=5)
        self.welcome_text.configure(state="disabled")

        paths_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        paths_frame.grid(row=1, column=0, pady=5, padx=10, sticky="ew")
        paths_frame.grid_columnconfigure(1, weight=1)

        self.anomaly_label = ctk.CTkLabel(paths_frame, text="")
        self.anomaly_label.grid(row=0, column=0, sticky="w", pady=2)
        self.anomaly_entry = ctk.CTkEntry(paths_frame, placeholder_text="C:/Anomaly")
        self.anomaly_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.anomaly_browse_button = ctk.CTkButton(
            paths_frame,
            text="",
            width=100,
            command=lambda: self._browse_path(self.anomaly_entry),
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE
        )
        self.anomaly_browse_button.grid(row=0, column=2, pady=2)

        self.gamma_label = ctk.CTkLabel(paths_frame, text="")
        self.gamma_label.grid(row=1, column=0, sticky="w", pady=2)
        self.gamma_entry = ctk.CTkEntry(paths_frame, placeholder_text="C:/GAMMA")
        self.gamma_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.gamma_browse_button = ctk.CTkButton(
            paths_frame,
            text="",
            width=100,
            command=lambda: self._browse_path(self.gamma_entry),
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE
        )
        self.gamma_browse_button.grid(row=1, column=2, pady=2)

        self.cache_label = ctk.CTkLabel(paths_frame, text="")
        self.cache_label.grid(row=2, column=0, sticky="w", pady=2)
        self.cache_entry = ctk.CTkEntry(paths_frame, placeholder_text="(Optional)")
        self.cache_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        self.cache_browse_button = ctk.CTkButton(
            paths_frame,
            text="",
            width=100,
            command=lambda: self._browse_path(self.cache_entry),
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE
        )
        self.cache_browse_button.grid(row=2, column=2, pady=2)

        self.status_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.status_label.grid(row=2, column=0, pady=5, padx=10, sticky="ew")

        self.progress_label = ctk.CTkLabel(main_frame, text="")
        self.progress_label.grid(row=3, column=0, pady=2, padx=10, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(main_frame, progress_color=FLY_AGARIC_RED)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=4, column=0, pady=5, padx=10, sticky="ew")

        self.install_text = ctk.CTkTextbox(
            main_frame,
            fg_color=FLY_AGARIC_WHITE,
            text_color=FLY_AGARIC_BLACK,
            border_color=FLY_AGARIC_RED,
            border_width=2,
            wrap="word"
        )
        self.install_text.grid(row=5, column=0, pady=5, padx=10, sticky="nsew")

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=6, column=0, pady=10, padx=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.install_gamma_button = ctk.CTkButton(
            button_frame,
            text="",
            command=lambda: self._start_installation(False),
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE,
            text_color=FLY_AGARIC_WHITE,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.install_gamma_button.grid(row=0, column=0, sticky="ew", padx=2)

        self.install_both_button = ctk.CTkButton(
            button_frame,
            text="",
            command=lambda: self._start_installation(True),
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE,
            text_color=FLY_AGARIC_WHITE,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.install_both_button.grid(row=0, column=1, sticky="ew", padx=2)

        self.settings_button = ctk.CTkButton(
            button_frame,
            text="",
            command=self._open_settings,
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE
        )
        self.settings_button.grid(row=0, column=2, sticky="ew", padx=2)

        self.console_button = ctk.CTkButton(
            button_frame,
            text="",
            command=self._open_console,
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE
        )
        self.console_button.grid(row=0, column=3, sticky="ew", padx=2)

        self.about_button = ctk.CTkButton(
            button_frame,
            text="",
            command=self._open_about,
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE
        )
        self.about_button.grid(row=0, column=4, sticky="ew", padx=2)

        language_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        language_frame.grid(row=7, column=0, pady=5, padx=10, sticky="ew")

        self.language_label = ctk.CTkLabel(language_frame, text="")
        self.language_label.pack(side="left")

        self.language_option_menu = ctk.CTkOptionMenu(
            language_frame,
            values=["en", "ru"],
            command=self._on_language_select,
            fg_color=FLY_AGARIC_RED,
            button_color=FLY_AGARIC_RED,
            button_hover_color=FLY_AGARIC_WHITE
        )
        self.language_option_menu.set(self.translator.current_lang)
        self.language_option_menu.pack(side="right")

    def _browse_path(self, entry_widget):
        path = filedialog.askdirectory(title=self.translator.get("browse_button"))
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)

    def _load_paths_from_config(self):
        config = self.config_manager.get_config()
        if config.anomaly_path:
            self.anomaly_entry.insert(0, config.anomaly_path)
        if config.gamma_path:
            self.gamma_entry.insert(0, config.gamma_path)
        if config.cache_path:
            self.cache_entry.insert(0, config.cache_path)

    def _save_paths_to_config(self):
        anomaly_path = self.anomaly_entry.get().strip()
        gamma_path = self.gamma_entry.get().strip()
        cache_path = self.cache_entry.get().strip() or None

        self.config_manager.update(
            anomaly_path=anomaly_path,
            gamma_path=gamma_path,
            cache_path=cache_path
        )

    def _start_installation(self, install_ao: bool):
        anomaly_path = self.anomaly_entry.get().strip()
        gamma_path = self.gamma_entry.get().strip()

        if not anomaly_path or not gamma_path:
            messagebox.showerror(
                "Error",
                self.translator.get("error_paths_required")
            )
            return

        self._save_paths_to_config()
        self.install_ao_after = install_ao

        self.install_gamma_button.configure(state="disabled")
        self.install_both_button.configure(state="disabled")

        threading.Thread(target=self._run_installation, daemon=True).start()

    def _run_installation(self):
        try:
            config = self.config_manager.get_config()
            workflow = GammaWorkflow(config)

            def progress_callback(progress: InstallProgress):
                self._queue_ui_update(self.progress_bar.set, progress.progress_fraction)
                stage_text = self.translator.get(f"stage_{progress.stage}", progress.stage)
                self._queue_ui_update(self.progress_label.configure, text=stage_text)

            def status_callback(message: str):
                self._queue_ui_update(self._append_install_text, message)

            success = workflow.full_install(progress_callback, status_callback)

            if success:
                self._queue_ui_update(self.status_label.configure, text=self.translator.get("status_complete"))
                self._queue_ui_update(
                    messagebox.showinfo,
                    "Success",
                    self.translator.get("installation_success_message")
                )

                if self.install_ao_after:
                    self._queue_ui_update(self._launch_ao_launcher)

            else:
                self._queue_ui_update(self.status_label.configure, text=self.translator.get("status_error"))

        except Exception as e:
            logging.error(f"Installation failed: {e}", exc_info=True)
            self._queue_ui_update(self.status_label.configure, text=f"Error: {str(e)}")
        finally:
            self._queue_ui_update(self.install_gamma_button.configure, state="normal")
            self._queue_ui_update(self.install_both_button.configure, state="normal")

    def _append_install_text(self, message: str):
        self.install_text.configure(state="normal")
        self.install_text.insert("end", message + "\n")
        self.install_text.see("end")
        self.install_text.configure(state="disabled")

    def _launch_ao_launcher(self):
        workflow = GammaWorkflow(self.config_manager.get_config())
        if not workflow.launch_ao_launcher():
            messagebox.showwarning(
                "Warning",
                self.translator.get("ao_launcher_not_found")
            )

    def _open_settings(self):
        settings_window = SettingsWindow(self, self.config_manager)
        settings_window.grab_set()

    def _open_console(self):
        if self.console_window is None or not self.console_window.winfo_exists():
            self.console_window = ConsoleWindow(self)
        else:
            self.console_window.focus()

    def _open_about(self):
        about_window = AboutWindow(self)
        about_window.grab_set()

    def _on_language_select(self, language: str):
        self.translator.set_language(language)
        self.config_manager.update(language=language)
        self._update_ui_text()

    def _update_ui_text(self):
        self.title(self.translator.get("app_title"))

        self.welcome_label.configure(text=self.translator.get("welcome_title"))
        self.welcome_text.configure(state="normal")
        self.welcome_text.delete("1.0", "end")
        self.welcome_text.insert("1.0", self.translator.get("welcome_message"))
        self.welcome_text.configure(state="disabled")

        self.anomaly_label.configure(text=self.translator.get("anomaly_path_label"))
        self.gamma_label.configure(text=self.translator.get("gamma_path_label"))
        self.cache_label.configure(text=self.translator.get("cache_path_label"))

        self.anomaly_browse_button.configure(text=self.translator.get("browse_button"))
        self.gamma_browse_button.configure(text=self.translator.get("browse_button"))
        self.cache_browse_button.configure(text=self.translator.get("browse_button"))

        self.status_label.configure(text=self.translator.get("status_ready"))
        self.progress_label.configure(text=self.translator.get("progress_label"))

        self.install_gamma_button.configure(text=self.translator.get("install_gamma_only"))
        self.install_both_button.configure(text=self.translator.get("install_gamma_and_ao"))
        self.settings_button.configure(text=self.translator.get("settings_button"))
        self.console_button.configure(text=self.translator.get("console_button"))
        self.about_button.configure(text=self.translator.get("about_button"))
        self.language_label.configure(text=self.translator.get("language_switcher_label"))


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, config_manager: GammaConfigManager):
        super().__init__(master)
        self.config_manager = config_manager
        self.translator = get_translator()

        self.title(self.translator.get("settings_window_title"))
        self.geometry("500x300")

        config = self.config_manager.get_config()

        main_frame = ctk.CTkFrame(self, fg_color=FLY_AGARIC_BLACK, border_color=FLY_AGARIC_RED, border_width=2)
        main_frame.pack(pady=10, padx=10, fill="both", expand=True)
        main_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(main_frame, text=self.translator.get("mo_version_label")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.mo_version_entry = ctk.CTkEntry(main_frame)
        self.mo_version_entry.insert(0, config.mod_organizer_version)
        self.mo_version_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        self.install_mo_var = ctk.BooleanVar(value=config.install_mod_organizer)
        self.install_mo_checkbox = ctk.CTkCheckBox(
            main_frame,
            text=self.translator.get("install_mo_checkbox"),
            variable=self.install_mo_var
        )
        self.install_mo_checkbox.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(main_frame, text=self.translator.get("gamma_repo_label")).grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.gamma_repo_entry = ctk.CTkEntry(main_frame)
        self.gamma_repo_entry.insert(0, config.custom_gamma_repo)
        self.gamma_repo_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.save_button = ctk.CTkButton(
            button_frame,
            text=self.translator.get("save_button"),
            command=self._save_and_close,
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE
        )
        self.save_button.pack(side="left", padx=5)

        self.cancel_button = ctk.CTkButton(
            button_frame,
            text=self.translator.get("cancel_button"),
            command=self.destroy,
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE
        )
        self.cancel_button.pack(side="left", padx=5)

    def _save_and_close(self):
        self.config_manager.update(
            mod_organizer_version=self.mo_version_entry.get(),
            install_mod_organizer=self.install_mo_var.get(),
            custom_gamma_repo=self.gamma_repo_entry.get()
        )
        self.destroy()


class ConsoleWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.translator = get_translator()

        self.title(self.translator.get("console_window_title"))
        self.geometry("600x400")

        main_frame = ctk.CTkFrame(self, fg_color=FLY_AGARIC_BLACK, border_color=FLY_AGARIC_RED, border_width=2)
        main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.console_text = ctk.CTkTextbox(
            main_frame,
            fg_color=FLY_AGARIC_BLACK,
            text_color=FLY_AGARIC_WHITE,
            border_color=FLY_AGARIC_RED,
            border_width=2,
            wrap="word"
        )
        self.console_text.pack(fill="both", expand=True, padx=5, pady=5)

        for message in log_history:
            self.log(message)

    def log(self, message: str):
        self.console_text.configure(state="normal")
        self.console_text.insert("end", message + "\n")
        self.console_text.see("end")
        self.console_text.configure(state="disabled")


class AboutWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.translator = get_translator()

        self.title(self.translator.get("about_window_title"))
        self.geometry("500x350")

        main_frame = ctk.CTkFrame(self, fg_color=FLY_AGARIC_BLACK, border_color=FLY_AGARIC_RED, border_width=2)
        main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        about_text = ctk.CTkTextbox(
            main_frame,
            fg_color=FLY_AGARIC_WHITE,
            text_color=FLY_AGARIC_BLACK,
            border_color=FLY_AGARIC_RED,
            border_width=2,
            wrap="word"
        )
        about_text.pack(fill="both", expand=True, padx=10, pady=10)
        about_text.insert("1.0", self.translator.get("about_message"))
        about_text.configure(state="disabled")

        close_button = ctk.CTkButton(
            main_frame,
            text=self.translator.get("cancel_button"),
            command=self.destroy,
            fg_color=FLY_AGARIC_RED,
            hover_color=FLY_AGARIC_WHITE
        )
        close_button.pack(pady=5)
