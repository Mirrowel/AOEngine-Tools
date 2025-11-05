"""
Unit tests for GAMMA data models.
"""

import pytest
from datetime import datetime
from pathlib import Path
from pydantic import ValidationError

from launcher.core.gamma.models import (
    GammaConfig,
    ModType,
    ModRecord,
    SeparatorRecord,
    DownloadableModRecord,
    InstallationPhase,
    InstallationState,
)


class TestGammaConfig:
    """Tests for GammaConfig model."""

    def test_default_config(self):
        """Test default configuration."""
        config = GammaConfig()
        assert config.anomaly_path is None
        assert config.gamma_path is None
        assert config.cache_path is None
        assert config.mo2_version == "v2.4.4"
        assert config.preserve_user_ltx is False
        assert config.force_git_download is True
        assert config.check_md5 is True
        assert config.delete_reshade is True
        assert config.parallel_downloads == 4
        assert config.parallel_extractions == 2

    def test_config_validation(self):
        """Test configuration field validation."""
        # Valid range for parallel downloads
        config = GammaConfig(parallel_downloads=8)
        assert config.parallel_downloads == 8

        # Invalid range should fail
        with pytest.raises(ValidationError):
            GammaConfig(parallel_downloads=0)

        with pytest.raises(ValidationError):
            GammaConfig(parallel_downloads=10)

    def test_path_creation(self, tmp_path):
        """Test that paths are created if they don't exist."""
        anomaly_path = tmp_path / "anomaly"
        gamma_path = tmp_path / "gamma"
        cache_path = tmp_path / "cache"

        config = GammaConfig(
            anomaly_path=anomaly_path,
            gamma_path=gamma_path,
            cache_path=cache_path
        )

        assert anomaly_path.exists()
        assert gamma_path.exists()
        assert cache_path.exists()

    def test_is_anomaly_installed(self, tmp_path):
        """Test Anomaly installation detection."""
        anomaly_path = tmp_path / "anomaly"
        config = GammaConfig(anomaly_path=anomaly_path)

        # Not installed - missing directories
        assert not config.is_anomaly_installed()

        # Create required directories
        (anomaly_path / "bin").mkdir(parents=True)
        (anomaly_path / "gamedata").mkdir(parents=True)
        (anomaly_path / "appdata").mkdir(parents=True)

        # Still not installed - missing executable
        assert not config.is_anomaly_installed()

        # Create executable
        (anomaly_path / "bin" / "AnomalyDX9.exe").touch()

        # Still not installed - missing user.ltx
        assert not config.is_anomaly_installed()

        # Create user.ltx
        (anomaly_path / "appdata" / "user.ltx").touch()

        # Now it's installed
        assert config.is_anomaly_installed()

    def test_is_mo2_installed(self, tmp_path):
        """Test MO2 installation detection."""
        gamma_path = tmp_path / "gamma"
        config = GammaConfig(gamma_path=gamma_path)

        # Not installed
        assert not config.is_mo2_installed()

        # Create MO2 executable in parent directory
        mo2_root = gamma_path.parent
        mo2_root.mkdir(parents=True, exist_ok=True)
        (mo2_root / "ModOrganizer.exe").touch()

        # Now it's installed
        assert config.is_mo2_installed()


class TestModRecord:
    """Tests for ModRecord parsing."""

    def test_separator_parsing(self):
        """Test parsing separator records."""
        line = "=== CORE MODS ==="
        record = ModRecord.from_tsv_line(line)

        assert isinstance(record, SeparatorRecord)
        assert record.mod_name == "=== CORE MODS ==="
        assert record.mod_type == ModType.SEPARATOR

    def test_moddb_parsing(self):
        """Test parsing ModDB mod records."""
        line = "https://www.moddb.com/downloads/start/12345\t0\t.zip\tTest Mod - Author\thttps://www.moddb.com/mods/test\ttest-mod.zip\tabc123"
        record = ModRecord.from_tsv_line(line)

        assert isinstance(record, DownloadableModRecord)
        assert record.mod_type == ModType.MODDB
        assert record.url == "https://www.moddb.com/downloads/start/12345"
        assert record.instructions == "0"
        assert record.patch == ".zip"
        assert record.mod_name == "Test Mod - Author"
        assert record.info_url == "https://www.moddb.com/mods/test"
        assert record.archive_name == "test-mod.zip"
        assert record.md5_hash == "abc123"
        assert record.enabled is True

    def test_github_parsing(self):
        """Test parsing GitHub mod records."""
        line = "https://github.com/user/repo/archive/master.zip\tfolder1:folder2\t.zip\tGitHub Mod - Dev"
        record = ModRecord.from_tsv_line(line)

        assert isinstance(record, DownloadableModRecord)
        assert record.mod_type == ModType.GITHUB
        assert record.instructions == "folder1:folder2"

    def test_enabled_flag(self):
        """Test enabled flag in parsing."""
        line = "https://www.moddb.com/downloads/start/12345\t0\t.zip\tTest Mod"

        # Enabled
        record = ModRecord.from_tsv_line(line, enabled=True)
        assert record.enabled is True

        # Disabled
        record = ModRecord.from_tsv_line(line, enabled=False)
        assert record.enabled is False

    def test_invalid_url(self):
        """Test parsing with invalid URL."""
        line = "https://example.com/unknown\t0\t.zip\tUnknown Mod"

        with pytest.raises(ValueError, match="Unknown mod type"):
            ModRecord.from_tsv_line(line)


class TestDownloadableModRecord:
    """Tests for DownloadableModRecord."""

    def test_get_cache_path(self, tmp_path):
        """Test cache path generation."""
        mod = DownloadableModRecord(
            url="https://example.com/mod.zip",
            instructions="0",
            patch=".zip",
            mod_name="Test Mod",
            archive_name="test-mod.zip",
            mod_type=ModType.MODDB
        )

        cache_path = mod.get_cache_path(tmp_path)
        assert cache_path == tmp_path / "test-mod.zip"

    def test_get_cache_path_no_archive_name(self, tmp_path):
        """Test cache path generation without archive name."""
        mod = DownloadableModRecord(
            url="https://example.com/download/mod-file.zip",
            instructions="0",
            patch=".zip",
            mod_name="Test Mod",
            mod_type=ModType.MODDB
        )

        cache_path = mod.get_cache_path(tmp_path)
        assert cache_path == tmp_path / "mod-file.zip"

    def test_generate_meta_ini(self, tmp_path):
        """Test meta.ini generation."""
        mod = DownloadableModRecord(
            url="https://www.moddb.com/downloads/start/12345",
            instructions="0",
            patch=".zip",
            mod_name="Test Mod - Author",
            info_url="https://www.moddb.com/mods/test",
            mod_type=ModType.MODDB
        )

        meta_content = mod.generate_meta_ini(tmp_path)

        assert "gameName=stalkeranomaly" in meta_content
        assert "modid=0" in meta_content
        assert "ignoredversion=Test Mod - Author" in meta_content
        assert "url=https://www.moddb.com/mods/test" in meta_content
        assert "hasCustomURL=true" in meta_content


class TestSeparatorRecord:
    """Tests for SeparatorRecord."""

    def test_separator_creation(self):
        """Test separator record creation."""
        sep = SeparatorRecord(mod_name="=== TEST ===")

        assert sep.mod_name == "=== TEST ==="
        assert sep.mod_type == ModType.SEPARATOR

    def test_generate_meta_ini(self):
        """Test separator meta.ini generation."""
        sep = SeparatorRecord(mod_name="=== SECTION ===")
        meta_content = sep.generate_meta_ini(5)

        assert "gameName=stalkeranomaly" in meta_content
        assert "modid=0" in meta_content
        assert "category=-1" in meta_content


class TestInstallationState:
    """Tests for InstallationState."""

    def test_initial_state(self):
        """Test initial installation state."""
        state = InstallationState()

        assert state.phase == InstallationPhase.NOT_STARTED
        assert state.phase_progress == 0.0
        assert state.overall_progress == 0.0
        assert state.current_operation == ""
        assert state.total_mods == 0
        assert state.downloaded_mods == 0
        assert state.installed_mods == 0
        assert state.failed_mods == []
        assert state.errors == []
        assert state.warnings == []

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        state = InstallationState()

        # No start time
        assert state.get_elapsed_time() is None

        # With start time, no end time
        state.start_time = datetime.now()
        elapsed = state.get_elapsed_time()
        assert elapsed is not None
        assert elapsed >= 0

        # With end time
        state.end_time = datetime.now()
        elapsed = state.get_elapsed_time()
        assert elapsed is not None
        assert elapsed >= 0

    def test_estimated_time_remaining(self):
        """Test time estimation."""
        state = InstallationState()

        # No progress
        assert state.get_estimated_time_remaining() is None

        # Some progress
        state.start_time = datetime(2025, 1, 1, 12, 0, 0)
        state.end_time = datetime(2025, 1, 1, 12, 10, 0)  # 10 minutes elapsed
        state.overall_progress = 0.25  # 25% done

        remaining = state.get_estimated_time_remaining()
        assert remaining is not None
        # Should be about 30 minutes remaining (10 min / 0.25 * 0.75)
        assert 29 * 60 <= remaining <= 31 * 60

    def test_format_time(self):
        """Test time formatting."""
        state = InstallationState()

        assert state.format_time(None) == "Unknown"
        assert state.format_time(30) == "30s"
        assert state.format_time(90) == "1m 30s"
        assert state.format_time(3661) == "1h 1m 1s"

    def test_phase_transitions(self):
        """Test phase state transitions."""
        state = InstallationState()

        phases = [
            InstallationPhase.CHECKING_REQUIREMENTS,
            InstallationPhase.DOWNLOADING_ANOMALY,
            InstallationPhase.EXTRACTING_ANOMALY,
            InstallationPhase.DOWNLOADING_MODS,
            InstallationPhase.EXTRACTING_MODS,
            InstallationPhase.COMPLETED
        ]

        for phase in phases:
            state.phase = phase
            assert state.phase == phase

    def test_error_tracking(self):
        """Test error and warning tracking."""
        state = InstallationState()

        state.errors.append("Test error 1")
        state.errors.append("Test error 2")
        state.warnings.append("Test warning")

        assert len(state.errors) == 2
        assert len(state.warnings) == 1
        assert "Test error 1" in state.errors
        assert "Test warning" in state.warnings

    def test_mod_tracking(self):
        """Test mod installation tracking."""
        state = InstallationState()

        state.total_mods = 100
        state.downloaded_mods = 75
        state.installed_mods = 50
        state.failed_mods = ["Mod A", "Mod B"]

        assert state.total_mods == 100
        assert state.downloaded_mods == 75
        assert state.installed_mods == 50
        assert len(state.failed_mods) == 2
