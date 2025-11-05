"""
Unit tests for ModDB downloader.
"""

import pytest
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from launcher.core.gamma.moddb import (
    ModDBDownloader,
    ModDBError,
    ModDBScrapingError,
    ModDBDownloadError,
    HashMismatchError,
)


class TestModDBDownloader:
    """Tests for ModDB downloader."""

    @pytest.fixture
    def downloader(self):
        """Create downloader instance."""
        return ModDBDownloader(timeout=10)

    def test_initialization(self, downloader):
        """Test downloader initialization."""
        assert downloader.timeout == 10
        assert downloader.session is not None

    @patch('launcher.core.gamma.moddb.cloudscraper.create_scraper')
    def test_scrape_download_page_success(self, mock_scraper, downloader):
        """Test successful page scraping."""
        # Mock HTML response
        html_content = """
        <html>
            <a class="buttondownload" href="/downloads/start/12345">Download</a>
            <div class="row clear">
                <span>Filename:</span>
                <span>test-mod.zip</span>
            </div>
            <div class="row clear">
                <span>MD5 Hash:</span>
                <span>abc123def456</span>
            </div>
        </html>
        """

        mock_response = Mock()
        mock_response.text = html_content
        mock_response.raise_for_status = Mock()

        downloader.session.get = Mock(return_value=mock_response)

        url, filename, md5 = downloader.scrape_download_page("https://www.moddb.com/mods/test")

        assert url == "https://www.moddb.com/downloads/start/12345"
        assert filename == "test-mod.zip"
        assert md5 == "abc123def456"

    @patch('launcher.core.gamma.moddb.cloudscraper.create_scraper')
    def test_scrape_download_page_no_link(self, mock_scraper, downloader):
        """Test scraping when download link not found."""
        html_content = "<html><body>No download link</body></html>"

        mock_response = Mock()
        mock_response.text = html_content
        mock_response.raise_for_status = Mock()

        downloader.session.get = Mock(return_value=mock_response)

        # The retry decorator will retry 3 times, so we expect tenacity.RetryError
        from tenacity import RetryError
        with pytest.raises((ModDBScrapingError, RetryError)):
            downloader.scrape_download_page("https://www.moddb.com/mods/test")

    def test_extract_mirror_link_redirect(self, downloader):
        """Test mirror link extraction with redirect."""
        mock_response = Mock()
        mock_response.status_code = 302
        mock_response.headers = {'Location': 'https://cdn.moddb.com/files/test.zip'}

        downloader.session.get = Mock(return_value=mock_response)

        url = downloader.extract_mirror_link("https://www.moddb.com/downloads/mirror/12345")

        assert url == "https://cdn.moddb.com/files/test.zip"

    def test_extract_mirror_link_meta_refresh(self, downloader):
        """Test mirror link extraction with meta refresh."""
        html_content = """
        <html>
            <meta http-equiv="refresh" content="0;url=https://cdn.moddb.com/files/test.zip">
        </html>
        """

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_response.raise_for_status = Mock()

        downloader.session.get = Mock(return_value=mock_response)

        url = downloader.extract_mirror_link("https://www.moddb.com/downloads/mirror/12345")

        assert url == "https://cdn.moddb.com/files/test.zip"

    def test_calculate_md5(self, tmp_path, downloader):
        """Test MD5 hash calculation."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        expected_hash = hashlib.md5(test_content).hexdigest()
        actual_hash = downloader.calculate_md5(test_file)

        assert actual_hash == expected_hash

    def test_verify_hash_success(self, tmp_path, downloader):
        """Test successful hash verification."""
        test_file = tmp_path / "test.txt"
        test_content = b"Test content"
        test_file.write_bytes(test_content)

        expected_hash = hashlib.md5(test_content).hexdigest()

        assert downloader.verify_hash(test_file, expected_hash) is True

    def test_verify_hash_failure(self, tmp_path, downloader):
        """Test failed hash verification."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")

        wrong_hash = "wrong_hash_value"

        assert downloader.verify_hash(test_file, wrong_hash) is False

    def test_download_file_success(self, tmp_path, downloader):
        """Test successful file download."""
        output_file = tmp_path / "download.zip"
        test_content = b"File content"

        # Mock streaming response
        mock_response = Mock()
        mock_response.headers = {'content-length': str(len(test_content))}
        mock_response.iter_content = Mock(return_value=[test_content])
        mock_response.raise_for_status = Mock()

        downloader.session.get = Mock(return_value=mock_response)

        # Track progress calls
        progress_calls = []
        def progress_callback(downloaded, total):
            progress_calls.append((downloaded, total))

        downloader.download_file(
            "https://example.com/file.zip",
            output_file,
            progress_callback=progress_callback
        )

        assert output_file.exists()
        assert output_file.read_bytes() == test_content
        assert len(progress_calls) > 0

    def test_download_file_with_hash_verification(self, tmp_path, downloader):
        """Test download with hash verification."""
        output_file = tmp_path / "download.zip"
        test_content = b"File content"
        expected_hash = hashlib.md5(test_content).hexdigest()

        # Mock streaming response
        mock_response = Mock()
        mock_response.headers = {'content-length': str(len(test_content))}
        mock_response.iter_content = Mock(return_value=[test_content])
        mock_response.raise_for_status = Mock()

        downloader.session.get = Mock(return_value=mock_response)

        downloader.download_file(
            "https://example.com/file.zip",
            output_file,
            expected_md5=expected_hash
        )

        assert output_file.exists()

    def test_download_file_hash_mismatch(self, tmp_path, downloader):
        """Test download with hash mismatch."""
        output_file = tmp_path / "download.zip"
        test_content = b"File content"
        wrong_hash = "wrong_hash"

        # Mock streaming response
        mock_response = Mock()
        mock_response.headers = {'content-length': str(len(test_content))}
        mock_response.iter_content = Mock(return_value=[test_content])
        mock_response.raise_for_status = Mock()

        downloader.session.get = Mock(return_value=mock_response)

        # The retry decorator will retry 3 times, so we expect tenacity.RetryError
        from tenacity import RetryError
        with pytest.raises((HashMismatchError, RetryError)):
            downloader.download_file(
                "https://example.com/file.zip",
                output_file,
                expected_md5=wrong_hash
            )

        # File should be deleted on hash mismatch
        assert not output_file.exists()

    def test_download_mod_cached(self, tmp_path, downloader):
        """Test using cached mod file."""
        cache_file = tmp_path / "cached-mod.zip"
        test_content = b"Cached content"
        cache_file.write_bytes(test_content)

        expected_hash = hashlib.md5(test_content).hexdigest()

        # Should not make any HTTP requests
        downloader.session.get = Mock()

        downloader.download_mod(
            info_url="https://www.moddb.com/mods/test",
            download_url="https://www.moddb.com/downloads/start/12345",
            output_path=cache_file,
            expected_md5=expected_hash,
            use_cached=True
        )

        # Should not have made any requests
        downloader.session.get.assert_not_called()

    def test_download_mod_cache_invalid(self, tmp_path, downloader):
        """Test re-downloading when cache hash is invalid."""
        cache_file = tmp_path / "cached-mod.zip"
        cache_file.write_bytes(b"Old content")

        new_content = b"New content"
        expected_hash = hashlib.md5(new_content).hexdigest()

        # Mock scraping
        scrape_html = """
        <html>
            <a class="buttondownload" href="/downloads/start/12345">Download</a>
        </html>
        """

        # Mock mirror extraction
        mirror_html = """
        <html>
            <meta http-equiv="refresh" content="0;url=https://cdn.moddb.com/file.zip">
        </html>
        """

        # Mock download
        download_response = Mock()
        download_response.headers = {'content-length': str(len(new_content))}
        download_response.iter_content = Mock(return_value=[new_content])
        download_response.raise_for_status = Mock()

        # Setup mock responses
        responses = [
            # Scrape response
            Mock(text=scrape_html, raise_for_status=Mock()),
            # Mirror response
            Mock(status_code=200, text=mirror_html, raise_for_status=Mock()),
            # Download response
            download_response
        ]

        downloader.session.get = Mock(side_effect=responses)

        downloader.download_mod(
            info_url="https://www.moddb.com/mods/test",
            download_url="https://www.moddb.com/downloads/start/12345",
            output_path=cache_file,
            expected_md5=expected_hash,
            use_cached=True
        )

        # File should be updated
        assert cache_file.read_bytes() == new_content
