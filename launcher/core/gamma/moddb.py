"""
ModDB Download Handler

Handles downloading files from ModDB with CloudFlare bypass, mirror selection,
and MD5 hash verification. Uses cloudscraper to bypass anti-bot protection.
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import Optional, Tuple, Callable
from bs4 import BeautifulSoup
import cloudscraper
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class ModDBError(Exception):
    """Base exception for ModDB operations."""
    pass


class ModDBScrapingError(ModDBError):
    """Error during ModDB page scraping."""
    pass


class ModDBDownloadError(ModDBError):
    """Error during ModDB file download."""
    pass


class HashMismatchError(ModDBError):
    """Downloaded file hash doesn't match expected hash."""
    pass


class ModDBDownloader:
    """
    Handles downloading files from ModDB.

    This class manages the complete ModDB download workflow including:
    - CloudFlare protection bypass using cloudscraper
    - HTML parsing to extract download metadata
    - Mirror selection for optimal download speed
    - MD5 hash verification
    - Progress callbacks for UI updates

    Attributes:
        session: Cloudscraper session for anti-bot protection
        timeout: Request timeout in seconds
    """

    def __init__(self, timeout: int = 300):
        """
        Initialize ModDB downloader.

        Args:
            timeout: Request timeout in seconds (default: 300)
        """
        self.session = cloudscraper.create_scraper(
            browser={
                'custom': 'GAMMA-Launcher/2.0'
            }
        )
        self.timeout = timeout

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def scrape_download_page(self, info_url: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Scrape ModDB page for download metadata.

        Extracts the download link, filename, and MD5 hash from a ModDB page.
        Uses BeautifulSoup to parse HTML and find relevant metadata.

        Args:
            info_url: ModDB page URL (e.g., https://www.moddb.com/mods/...)

        Returns:
            Tuple of (download_url, filename, md5_hash)

        Raises:
            ModDBScrapingError: If scraping fails or metadata not found
        """
        logger.info(f"Scraping ModDB page: {info_url}")

        try:
            response = self.session.get(info_url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ModDBScrapingError(f"Failed to fetch ModDB page: {e}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find download link
        download_link = None
        download_button = soup.find('a', class_='buttondownload')
        if download_button and download_button.get('href'):
            download_link = download_button['href']
            if not download_link.startswith('http'):
                download_link = f"https://www.moddb.com{download_link}"

        if not download_link:
            raise ModDBScrapingError("Download link not found on ModDB page")

        # Find filename and MD5 hash
        filename = None
        md5_hash = None

        # Look for metadata in "row clear" divs
        for row in soup.find_all('div', class_='row clear'):
            spans = row.find_all('span')
            if len(spans) >= 2:
                label = spans[0].get_text(strip=True).lower()
                value = spans[1].get_text(strip=True)

                if 'filename' in label:
                    filename = value
                elif 'md5' in label or 'hash' in label:
                    md5_hash = value.lower()

        logger.info(f"Scraped metadata - URL: {download_link}, File: {filename}, MD5: {md5_hash}")
        return download_link, filename, md5_hash

    def extract_mirror_link(self, download_url: str, mirror: str = "default") -> str:
        """
        Extract actual download URL from ModDB mirror page.

        ModDB uses intermediate mirror pages that redirect to the actual file.
        This method follows the redirect and extracts the final download URL.

        Args:
            download_url: ModDB download page URL
            mirror: Mirror to use (default, cloudflare, fastly, etc.)

        Returns:
            Direct download URL

        Raises:
            ModDBScrapingError: If mirror link extraction fails
        """
        logger.info(f"Extracting mirror link from: {download_url}")

        try:
            # Fetch mirror page
            response = self.session.get(download_url, timeout=self.timeout, allow_redirects=False)

            # Check for immediate redirect (some files)
            if response.status_code in (301, 302, 303, 307, 308):
                return response.headers['Location']

            # Parse page for redirect URL
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for meta refresh
            meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
            if meta_refresh:
                content = meta_refresh.get('content', '')
                match = re.search(r'url=(.*)', content, re.IGNORECASE)
                if match:
                    return match.group(1)

            # Look for JavaScript redirect
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    match = re.search(r'window\.location\.href\s*=\s*["\']([^"\']+)["\']', script.string)
                    if match:
                        return match.group(1)

            raise ModDBScrapingError("Could not extract mirror link from page")

        except requests.RequestException as e:
            raise ModDBScrapingError(f"Failed to extract mirror link: {e}")

    def calculate_md5(self, file_path: Path) -> str:
        """
        Calculate MD5 hash of a file.

        Reads file in chunks to handle large files efficiently.

        Args:
            file_path: Path to file

        Returns:
            MD5 hash as lowercase hex string
        """
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                md5.update(chunk)
        return md5.hexdigest()

    def verify_hash(self, file_path: Path, expected_hash: str) -> bool:
        """
        Verify file MD5 hash.

        Args:
            file_path: Path to file
            expected_hash: Expected MD5 hash (lowercase hex)

        Returns:
            True if hash matches, False otherwise
        """
        actual_hash = self.calculate_md5(file_path)
        logger.info(f"Hash verification - Expected: {expected_hash}, Actual: {actual_hash}")
        return actual_hash == expected_hash.lower()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def download_file(
        self,
        url: str,
        output_path: Path,
        expected_md5: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        Download file from URL with progress tracking and hash verification.

        Args:
            url: Download URL
            output_path: Where to save the file
            expected_md5: Expected MD5 hash for verification (optional)
            progress_callback: Called with (bytes_downloaded, total_bytes)

        Raises:
            ModDBDownloadError: If download fails
            HashMismatchError: If hash verification fails
        """
        logger.info(f"Downloading {url} to {output_path}")

        try:
            # Start download with streaming
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            # Get total file size
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Download with progress
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)

            logger.info(f"Download complete: {output_path} ({downloaded} bytes)")

            # Verify hash if provided
            if expected_md5:
                if not self.verify_hash(output_path, expected_md5):
                    output_path.unlink()  # Delete corrupted file
                    raise HashMismatchError(
                        f"Hash mismatch for {output_path.name}. "
                        f"Expected: {expected_md5}, got different hash."
                    )
                logger.info("Hash verification passed")

        except requests.RequestException as e:
            if output_path.exists():
                output_path.unlink()  # Clean up partial download
            raise ModDBDownloadError(f"Download failed: {e}")

    def download_mod(
        self,
        info_url: str,
        download_url: str,
        output_path: Path,
        expected_md5: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        use_cached: bool = True
    ) -> None:
        """
        Complete ModDB mod download workflow.

        This is the main entry point for downloading a mod from ModDB.
        It handles scraping, mirror extraction, download, and verification.

        Args:
            info_url: ModDB page URL for metadata
            download_url: Initial download URL
            output_path: Where to save the file
            expected_md5: Expected MD5 hash (optional, will scrape if not provided)
            progress_callback: Progress callback (bytes_downloaded, total_bytes)
            use_cached: Skip download if file exists and hash matches

        Raises:
            ModDBScrapingError: If scraping fails
            ModDBDownloadError: If download fails
            HashMismatchError: If hash verification fails
        """
        # Check if file already exists and is valid
        if use_cached and output_path.exists():
            if expected_md5:
                if self.verify_hash(output_path, expected_md5):
                    logger.info(f"Using cached file: {output_path}")
                    return
                else:
                    logger.warning(f"Cached file hash mismatch, re-downloading: {output_path}")
                    output_path.unlink()
            else:
                logger.info(f"Using cached file (no hash check): {output_path}")
                return

        # Scrape page for metadata if needed
        scraped_md5 = None
        if not expected_md5 and info_url:
            try:
                _, _, scraped_md5 = self.scrape_download_page(info_url)
                expected_md5 = scraped_md5
            except ModDBScrapingError as e:
                logger.warning(f"Failed to scrape MD5 hash: {e}")

        # Extract actual download link
        try:
            mirror_url = self.extract_mirror_link(download_url)
        except ModDBScrapingError:
            # Fallback: try direct download
            logger.warning("Mirror extraction failed, trying direct download")
            mirror_url = download_url

        # Download file
        self.download_file(mirror_url, output_path, expected_md5, progress_callback)
