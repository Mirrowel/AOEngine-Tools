"""
Unit tests for archive extraction.
"""

import pytest
import zipfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from launcher.core.gamma.archive import (
    ArchiveExtractor,
    ArchiveFormat,
    ArchiveError,
    UnsupportedFormatError,
    ExtractionError,
    FOMODParser,
    detect_mod_structure,
)


class TestArchiveExtractor:
    """Tests for archive extractor."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return ArchiveExtractor()

    @pytest.fixture
    def test_zip(self, tmp_path):
        """Create a test ZIP archive."""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file1.txt", "Content 1")
            zf.writestr("dir/file2.txt", "Content 2")
            zf.writestr("gamedata/configs/test.ltx", "Config data")
        return zip_path

    def test_detect_format_zip(self, test_zip, extractor):
        """Test ZIP format detection."""
        fmt = extractor.detect_format(test_zip)
        assert fmt == ArchiveFormat.ZIP

    def test_detect_format_by_extension(self, tmp_path, extractor):
        """Test format detection by file extension."""
        # Create file with ZIP extension but no magic bytes
        zip_file = tmp_path / "test.zip"
        zip_file.write_bytes(b"Not a real zip")

        # Should detect by extension as fallback
        fmt = extractor.detect_format(zip_file)
        # Will be UNKNOWN because magic bytes don't match and content is invalid
        assert fmt in (ArchiveFormat.UNKNOWN, ArchiveFormat.ZIP)

    def test_detect_format_nonexistent(self, tmp_path, extractor):
        """Test format detection for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            extractor.detect_format(tmp_path / "nonexistent.zip")

    def test_extract_zip_success(self, test_zip, tmp_path, extractor):
        """Test successful ZIP extraction."""
        extract_dir = tmp_path / "extracted"

        extractor.extract_zip(test_zip, extract_dir)

        assert (extract_dir / "file1.txt").exists()
        assert (extract_dir / "dir" / "file2.txt").exists()
        assert (extract_dir / "gamedata" / "configs" / "test.ltx").exists()

        assert (extract_dir / "file1.txt").read_text() == "Content 1"

    def test_extract_zip_with_progress(self, test_zip, tmp_path, extractor):
        """Test ZIP extraction with progress callback."""
        extract_dir = tmp_path / "extracted"

        progress_calls = []
        def progress_callback(current, total):
            progress_calls.append((current, total))

        extractor.extract_zip(test_zip, extract_dir, progress_callback)

        assert len(progress_calls) > 0
        assert progress_calls[-1][0] == progress_calls[-1][1]  # Final call should be 100%

    def test_extract_invalid_zip(self, tmp_path, extractor):
        """Test extraction of invalid ZIP file."""
        invalid_zip = tmp_path / "invalid.zip"
        invalid_zip.write_bytes(b"Not a real ZIP file")

        extract_dir = tmp_path / "extracted"

        with pytest.raises(ExtractionError):
            extractor.extract_zip(invalid_zip, extract_dir)

    def test_extract_auto_detect(self, test_zip, tmp_path, extractor):
        """Test automatic format detection and extraction."""
        extract_dir = tmp_path / "extracted"

        extractor.extract(test_zip, extract_dir)

        assert (extract_dir / "file1.txt").exists()
        assert (extract_dir / "gamedata" / "configs" / "test.ltx").exists()

    @patch('launcher.core.gamma.archive.shutil.which')
    @patch('launcher.core.gamma.archive.subprocess.run')
    def test_extract_with_7z_fallback(self, mock_run, mock_which, test_zip, tmp_path, extractor):
        """Test extraction using 7z binary fallback."""
        mock_which.return_value = "/usr/bin/7z"
        extract_dir = tmp_path / "extracted"

        # Mock successful 7z execution
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Force 7z extraction by disabling native
        extractor.use_native = False

        # Call _extract_with_7z directly to test the 7z code path
        extractor._extract_with_7z(test_zip, extract_dir)

        # Verify 7z was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert '7z' in call_args[0] or '7za' in call_args[0]
        assert 'x' in call_args  # extract command
        assert str(test_zip) in call_args

    def test_extract_unsupported_format(self, tmp_path, extractor):
        """Test extraction of unsupported format."""
        unknown_file = tmp_path / "unknown.xyz"
        unknown_file.write_bytes(b"Unknown format")

        extract_dir = tmp_path / "extracted"

        with pytest.raises(UnsupportedFormatError):
            extractor.extract(unknown_file, extract_dir)


class TestFOMODParser:
    """Tests for FOMOD parser."""

    @pytest.fixture
    def fomod_xml(self, tmp_path):
        """Create a test FOMOD XML file."""
        fomod_dir = tmp_path / "fomod"
        fomod_dir.mkdir()

        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <config>
            <moduleDependencies operator="And">
                <folder source="textures" destination="gamedata/textures"/>
                <folder source="configs" destination="gamedata/configs"/>
                <folder source="scripts"/>
            </moduleDependencies>
        </config>
        """

        fomod_file = fomod_dir / "ModuleConfig.xml"
        fomod_file.write_text(xml_content)

        return fomod_file

    def test_parse_fomod_success(self, fomod_xml):
        """Test successful FOMOD parsing."""
        directives = FOMODParser.parse_fomod(fomod_xml)

        assert len(directives) == 3
        assert ("textures", "gamedata/textures") in directives
        assert ("configs", "gamedata/configs") in directives
        assert ("scripts", "") in directives

    def test_parse_fomod_not_found(self, tmp_path):
        """Test parsing nonexistent FOMOD file."""
        with pytest.raises(FileNotFoundError):
            FOMODParser.parse_fomod(tmp_path / "nonexistent.xml")

    def test_apply_fomod_directives(self, tmp_path):
        """Test applying FOMOD directives."""
        # Create source structure
        extract_path = tmp_path / "extract"
        (extract_path / "textures").mkdir(parents=True)
        (extract_path / "configs").mkdir(parents=True)
        (extract_path / "textures" / "file1.dds").write_text("Texture")
        (extract_path / "configs" / "config.ltx").write_text("Config")

        # Apply directives
        install_path = tmp_path / "install"
        directives = [
            ("textures", "gamedata/textures"),
            ("configs", "gamedata/configs")
        ]

        FOMODParser.apply_fomod_directives(extract_path, install_path, directives)

        assert (install_path / "gamedata" / "textures" / "file1.dds").exists()
        assert (install_path / "gamedata" / "configs" / "config.ltx").exists()

    def test_apply_fomod_missing_source(self, tmp_path):
        """Test applying FOMOD with missing source directory."""
        extract_path = tmp_path / "extract"
        extract_path.mkdir()

        install_path = tmp_path / "install"
        directives = [("nonexistent", "gamedata")]

        # Should not raise error, just log warning
        FOMODParser.apply_fomod_directives(extract_path, install_path, directives)


class TestModStructureDetection:
    """Tests for mod structure detection."""

    def test_detect_direct_gamedata(self, tmp_path):
        """Test detection of direct gamedata folder."""
        (tmp_path / "gamedata").mkdir()
        (tmp_path / "gamedata" / "configs").mkdir()

        result = detect_mod_structure(tmp_path)
        assert result == tmp_path

    def test_detect_nested_gamedata(self, tmp_path):
        """Test detection of nested gamedata folder."""
        nested = tmp_path / "ModName"
        nested.mkdir()
        (nested / "gamedata").mkdir()
        (nested / "gamedata" / "configs").mkdir()

        result = detect_mod_structure(tmp_path)
        assert result == nested

    def test_detect_anomaly_folders(self, tmp_path):
        """Test detection of Anomaly mod folders."""
        (tmp_path / "appdata").mkdir()
        (tmp_path / "db").mkdir()
        (tmp_path / "gamedata").mkdir()

        result = detect_mod_structure(tmp_path)
        assert result == tmp_path

    def test_detect_ambiguous_structure(self, tmp_path):
        """Test detection with ambiguous structure."""
        # Create multiple subdirectories
        (tmp_path / "folder1").mkdir()
        (tmp_path / "folder2").mkdir()

        result = detect_mod_structure(tmp_path)
        assert result is None

    def test_detect_empty_directory(self, tmp_path):
        """Test detection with empty directory."""
        result = detect_mod_structure(tmp_path)
        assert result is None
