"""
1337x Torrent Scraper Module
Scrapes torrent information and magnet links from 1337x.to
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)


class Scraper1337x:
    """Scraper for 1337x.to torrent site"""
    
    def __init__(self, base_url: str = 'https://1337x.to', timeout: int = 30):
        """
        Initialize 1337x scraper
        
        Args:
            base_url: Base URL for 1337x
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search(
        self,
        query: str,
        category: str = 'all',
        max_results: int = 50
    ) -> List[Dict]:
        """
        Search for torrents on 1337x
        
        Args:
            query: Search query
            category: Category to search (all, movies, tv, etc.)
            max_results: Maximum number of results
        
        Returns:
            List of torrent dictionaries
        """
        try:
            results = []
            encoded_query = quote(query)
            search_url = f"{self.base_url}/search/{encoded_query}/1/"
            
            logger.info(f"Searching 1337x for: {query}")
            
            response = self.session.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all torrent rows
            table = soup.find('table', class_='table-list')
            if not table:
                logger.warning("No results table found")
                return []
            
            tbody = table.find('tbody')
            if not tbody:
                return []
            
            rows = tbody.find_all('tr')
            
            for row in rows[:max_results]:
                try:
                    torrent_data = self._parse_row(row)
                    if torrent_data:
                        results.append(torrent_data)
                except Exception as e:
                    logger.error(f"Error parsing row: {e}")
                    continue
            
            logger.info(f"Found {len(results)} results on 1337x")
            return results
            
        except requests.RequestException as e:
            logger.error(f"Error searching 1337x: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in 1337x search: {e}")
            return []
    
    def _parse_row(self, row) -> Optional[Dict]:
        """
        Parse a torrent row from search results
        
        Args:
            row: BeautifulSoup row element
        
        Returns:
            Dict with torrent information
        """
        try:
            # Get name and URL
            name_cell = row.find('td', class_='coll-1')
            if not name_cell:
                return None
            
            name_links = name_cell.find_all('a')
            if len(name_links) < 2:
                return None
            
            torrent_link = name_links[1]
            name = torrent_link.text.strip()
            torrent_url = urljoin(self.base_url, torrent_link['href'])
            
            # Get seeders
            seeds_cell = row.find('td', class_='coll-2')
            seeds = int(seeds_cell.text.strip()) if seeds_cell else 0
            
            # Get leechers
            leeches_cell = row.find('td', class_='coll-3')
            leeches = int(leeches_cell.text.strip()) if leeches_cell else 0
            
            # Get size
            size_cell = row.find('td', class_='coll-4')
            size_text = size_cell.text.strip() if size_cell else '0 B'
            size_gb = self._parse_size(size_text)
            
            # Get date
            date_cell = row.find('td', class_='coll-date')
            date = date_cell.text.strip() if date_cell else 'Unknown'
            
            # Get uploader
            uploader_cell = row.find('td', class_='coll-5')
            uploader = uploader_cell.text.strip() if uploader_cell else 'Unknown'
            
            return {
                'name': name,
                'url': torrent_url,
                'seeds': seeds,
                'leeches': leeches,
                'size': size_text,
                'size_gb': size_gb,
                'date': date,
                'uploader': uploader,
                'source': '1337x',
                'magnet_link': None  # Will be fetched later if needed
            }
            
        except Exception as e:
            logger.error(f"Error parsing torrent row: {e}")
            return None
    
    def get_magnet_link(self, torrent_url: str) -> Optional[str]:
        """
        Get magnet link from torrent page
        
        Args:
            torrent_url: URL to torrent detail page
        
        Returns:
            Magnet link or None
        """
        try:
            response = self.session.get(torrent_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find magnet link
            magnet_link = soup.find('a', href=re.compile(r'^magnet:\?'))
            
            if magnet_link:
                return magnet_link['href']
            
            logger.warning(f"No magnet link found for {torrent_url}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting magnet link: {e}")
            return None
    
    def get_torrent_details(self, torrent_url: str) -> Optional[Dict]:
        """
        Get detailed information from torrent page
        
        Args:
            torrent_url: URL to torrent detail page
        
        Returns:
            Dict with detailed torrent information
        """
        try:
            response = self.session.get(torrent_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get magnet link
            magnet_link = soup.find('a', href=re.compile(r'^magnet:\?'))
            magnet = magnet_link['href'] if magnet_link else None
            
            # Get torrent hash from magnet link
            torrent_hash = None
            if magnet:
                hash_match = re.search(r'btih:([a-fA-F0-9]{40})', magnet)
                if hash_match:
                    torrent_hash = hash_match.group(1).lower()
            
            # Get file list
            files = []
            file_list = soup.find('div', class_='file-content')
            if file_list:
                file_items = file_list.find_all('li')
                for item in file_items:
                    files.append(item.text.strip())
            
            return {
                'magnet_link': magnet,
                'hash': torrent_hash,
                'files': files
            }
            
        except Exception as e:
            logger.error(f"Error getting torrent details: {e}")
            return None
    
    @staticmethod
    def _parse_size(size_str: str) -> float:
        """
        Parse size string to GB
        
        Args:
            size_str: Size string (e.g., "1.5 GB", "500 MB")
        
        Returns:
            Size in GB
        """
        try:
            size_str = size_str.upper()
            match = re.search(r'([\d.]+)\s*(GB|MB|KB|B)', size_str)
            
            if not match:
                return 0.0
            
            value = float(match.group(1))
            unit = match.group(2)
            
            conversions = {
                'GB': 1,
                'MB': 1/1024,
                'KB': 1/(1024**2),
                'B': 1/(1024**3)
            }
            
            return value * conversions.get(unit, 0)
            
        except Exception:
            return 0.0
    
    def search_with_magnets(
        self,
        query: str,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Search and fetch magnet links for results
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of torrents with magnet links
        """
        results = self.search(query, max_results=max_results)
        
        for result in results:
            if result.get('url'):
                details = self.get_torrent_details(result['url'])
                if details:
                    result['magnet_link'] = details.get('magnet_link')
                    result['hash'] = details.get('hash')
                    result['files'] = details.get('files', [])
        
        return results