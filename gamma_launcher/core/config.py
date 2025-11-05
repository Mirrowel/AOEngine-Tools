import json
from pathlib import Path
from typing import Callable

from gamma_launcher.core.models import GammaConfig


class GammaConfigManager:
    """Manages persistence of the Gamma Launcher configuration."""

    def __init__(self, config_path: Path | None = None) -> None:
        if config_path is None:
            config_path = Path.cwd() / "gamma_config.json"
        self._config_path = config_path
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config = self._load()
        self._listeners: list[Callable[[GammaConfig], None]] = []

    def _load(self) -> GammaConfig:
        if not self._config_path.exists():
            return GammaConfig()
        try:
            data = json.loads(self._config_path.read_text(encoding="utf-8"))
            return GammaConfig(**data)
        except Exception:
            return GammaConfig()

    def get_config(self) -> GammaConfig:
        return self._config

    def save(self) -> None:
        self._config_path.write_text(self._config.model_dump_json(indent=4), encoding="utf-8")

    def update(self, **kwargs) -> GammaConfig:
        self._config = self._config.model_copy(update=kwargs)
        self.save()
        for listener in self._listeners:
            listener(self._config)
        return self._config

    def add_listener(self, listener: Callable[[GammaConfig], None]) -> None:
        self._listeners.append(listener)
