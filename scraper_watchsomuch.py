"""
WatchSoMuch Torrent Scraper Module
Scrapes torrent information from WatchSoMuch.to (public access)
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)


class ScraperWatchSoMuch:
    """Scraper for WatchSoMuch.to torrent site (public access)"""
    
    def __init__(
        self,
        base_url: str = 'https://watchsomuch.to',
        timeout: int = 30
    ):
        """
        Initialize WatchSoMuch scraper
        
        Args:
            base_url: Base URL for WatchSoMuch
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': base_url
        })
        logger.info("Initialized WatchSoMuch scraper (public access)")
    
    def search(
        self,
        query: str,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Search for torrents on WatchSoMuch
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of torrent dictionaries
        """
        try:
            results = []
            encoded_query = quote(query)
            search_url = f"{self.base_url}/Search/{encoded_query}"
            
            logger.info(f"Searching WatchSoMuch for: {query}")
            
            response = self.session.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find torrent results
            torrent_items = soup.find_all('div', class_='episode-block')
            
            if not torrent_items:
                # Try alternative structure
                torrent_items = soup.find_all('div', class_='torrent-item')
            
            if not torrent_items:
                logger.warning("No results found on WatchSoMuch")
                return []
            
            for item in torrent_items[:max_results]:
                try:
                    torrent_data = self._parse_item(item)
                    if torrent_data:
                        results.append(torrent_data)
                except Exception as e:
                    logger.error(f"Error parsing item: {e}")
                    continue
            
            logger.info(f"Found {len(results)} results on WatchSoMuch")
            return results
            
        except requests.RequestException as e:
            logger.error(f"Error searching WatchSoMuch: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in WatchSoMuch search: {e}")
            return []
    
    def _parse_item(self, item) -> Optional[Dict]:
        """
        Parse a torrent item from search results
        
        Args:
            item: BeautifulSoup item element
        
        Returns:
            Dict with torrent information
        """
        try:
            # Get title/name
            title_elem = item.find(['h3', 'h4', 'a'])
            if not title_elem:
                return None
            
            name = title_elem.text.strip()
            
            # Get torrent link
            torrent_link = item.find('a', href=re.compile(r'/(Watch|torrent|episode)/'))
            if not torrent_link:
                return None
            
            torrent_url = urljoin(self.base_url, torrent_link['href'])
            
            # Get quality info
            quality_elem = item.find('span', class_='quality')
            quality = quality_elem.text.strip() if quality_elem else 'Unknown'
            
            # Get size
            size_elem = item.find('span', class_='size')
            size_text = size_elem.text.strip() if size_elem else '0 B'
            size_gb = self._parse_size(size_text)
            
            # Get seeds/peers (if available)
            seeds_elem = item.find('span', class_='seeds')
            seeds = int(seeds_elem.text.strip()) if seeds_elem else 0
            
            peers_elem = item.find('span', class_='peers')
            leeches = int(peers_elem.text.strip()) if peers_elem else 0
            
            return {
                'name': name,
                'url': torrent_url,
                'quality': quality,
                'seeds': seeds,
                'leeches': leeches,
                'size': size_text,
                'size_gb': size_gb,
                'source': 'watchsomuch',
                'magnet_link': None,
                'hash': None
            }
            
        except Exception as e:
            logger.error(f"Error parsing torrent item: {e}")
            return None
    
    def get_torrent_details(self, torrent_url: str) -> Optional[Dict]:
        """
        Get detailed information from torrent page
        
        Args:
            torrent_url: URL to torrent detail page
        
        Returns:
            Dict with detailed torrent information including magnet link
        """
        try:
            response = self.session.get(torrent_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for magnet link
            magnet_link = soup.find('a', href=re.compile(r'^magnet:\?'))
            magnet = magnet_link['href'] if magnet_link else None
            
            # Get torrent hash from magnet link
            torrent_hash = None
            if magnet:
                hash_match = re.search(r'btih:([a-fA-F0-9]{40})', magnet)
                if hash_match:
                    torrent_hash = hash_match.group(1).lower()
            
            # Look for download button
            if not magnet:
                download_btn = soup.find('a', class_=['download-torrent', 'btn-download'])
                if download_btn and download_btn.get('href'):
                    # Check if it's a magnet link
                    href = download_btn['href']
                    if href.startswith('magnet:'):
                        magnet = href
                        hash_match = re.search(r'btih:([a-fA-F0-9]{40})', magnet)
                        if hash_match:
                            torrent_hash = hash_match.group(1).lower()
            
            # Get additional metadata
            info_table = soup.find('table', class_='info-table')
            metadata = {}
            
            if info_table:
                rows = info_table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].text.strip().lower()
                        value = cells[1].text.strip()
                        metadata[key] = value
            
            return {
                'magnet_link': magnet,
                'hash': torrent_hash,
                'metadata': metadata
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
    
    def search_with_details(
        self,
        query: str,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Search and fetch detailed information including magnet links
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of torrents with complete details
        """
        results = self.search(query, max_results=max_results)
        
        for result in results:
            if result.get('url'):
                details = self.get_torrent_details(result['url'])
                if details:
                    result['magnet_link'] = details.get('magnet_link')
                    result['hash'] = details.get('hash')
                    result['metadata'] = details.get('metadata', {})
        
        return results