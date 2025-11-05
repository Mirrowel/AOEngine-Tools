import requests
import logging
from pathlib import Path
from typing import Callable, Optional
from bs4 import BeautifulSoup
import cloudscraper
from tenacity import retry, stop_after_attempt, wait_exponential


class Downloader:
    """Handles downloading files with progress reporting and retry logic."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.scraper = cloudscraper.create_scraper()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def download_file(
        self,
        url: str,
        dest_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> Path:
        """Downloads a file from URL to dest_path with progress reporting."""
        if status_callback:
            status_callback(f"Downloading {url}")
        
        logging.info(f"Downloading from {url} to {dest_path}")
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        response = self.session.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size:
                        progress_callback(downloaded / total_size)
        
        if progress_callback:
            progress_callback(1.0)
        
        logging.info(f"Download complete: {dest_path}")
        return dest_path

    def get_moddb_download_link(self, info_url: str, download_url: str) -> str:
        """Extracts actual download link from ModDB page."""
        try:
            response = self.scraper.get(info_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            download_link = soup.find('a', {'id': 'downloadon'})
            if download_link and download_link.get('href'):
                return download_link['href']
        except Exception as e:
            logging.warning(f"Could not parse ModDB page: {e}")
        
        return download_url

    def download_github_release(
        self,
        repo_url: str,
        dest_path: Path,
        branch: str = "main",
        progress_callback: Optional[Callable[[float], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> Path:
        """Downloads a GitHub repository as a zip archive."""
        # Extract owner/repo from URL
        parts = repo_url.rstrip('/').split('/')
        if 'github.com' in repo_url:
            owner_repo = '/'.join(parts[-2:])
        else:
            owner_repo = repo_url
        
        zip_url = f"https://github.com/{owner_repo}/archive/refs/heads/{branch}.zip"
        return self.download_file(zip_url, dest_path, progress_callback, status_callback)
