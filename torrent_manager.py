"""
Torrent Manager Module
Core orchestration layer for torrent management
"""

import json
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from qbittorrent_client import QBittorrentClient
from scraper_1337x import Scraper1337x
from scraper_watchsomuch import ScraperWatchSoMuch
from config import Config

logger = logging.getLogger(__name__)


class TorrentManager:
    """Main orchestrator for torrent management"""
    
    def __init__(
        self,
        qb_host: str,
        qb_port: int,
        qb_username: str,
        qb_password: str
    ):
        """
        Initialize torrent manager
        
        Args:
            qb_host: qBittorrent host
            qb_port: qBittorrent port
            qb_username: qBittorrent username
            qb_password: qBittorrent password
        """
        self.qb_client = QBittorrentClient(
            host=qb_host,
            port=qb_port,
            username=qb_username,
            password=qb_password
        )
        
        # Initialize scrapers
        self.scraper_1337x = Scraper1337x(
            base_url=Config.LEETX_BASE_URL,
            timeout=Config.SEARCH_TIMEOUT
        )
        
        self.scraper_watchsomuch = ScraperWatchSoMuch(
            base_url=Config.WATCHSOMUCH_BASE_URL,
            timeout=Config.SEARCH_TIMEOUT
        )
        
        # Load blacklist and history
        self.blacklist_file = Path(Config.BLACKLIST_FILE)
        self.history_file = Path(Config.TORRENT_HISTORY_FILE)
        self.blacklist = self._load_blacklist()
        self.history = self._load_history()
    
    def search_torrents(
        self,
        query: str,
        quality: str = '',
        min_size_gb: float = 0,
        max_size_gb: float = float('inf'),
        sources: List[str] = None
    ) -> List[Dict]:
        """
        Search for torrents across multiple sources
        
        Args:
            query: Search query
            quality: Desired quality (720p, 1080p, etc.)
            min_size_gb: Minimum size in GB
            max_size_gb: Maximum size in GB
            sources: List of sources to search
        
        Returns:
            List of filtered torrent results
        """
        if sources is None:
            sources = []
            if Config.ENABLE_1337X:
                sources.append('1337x')
            if Config.ENABLE_WATCHSOMUCH:
                sources.append('watchsomuch')
        
        all_results = []
        
        # Search 1337x
        if '1337x' in sources and Config.ENABLE_1337X:
            try:
                results = self.scraper_1337x.search_with_magnets(
                    query=query,
                    max_results=Config.MAX_SEARCH_RESULTS
                )
                all_results.extend(results)
                logger.info(f"1337x returned {len(results)} results")
            except Exception as e:
                logger.error(f"Error searching 1337x: {e}")
        
        # Search WatchSoMuch
        if 'watchsomuch' in sources and Config.ENABLE_WATCHSOMUCH:
            try:
                results = self.scraper_watchsomuch.search_with_details(
                    query=query,
                    max_results=Config.MAX_SEARCH_RESULTS
                )
                all_results.extend(results)
                logger.info(f"WatchSoMuch returned {len(results)} results")
            except Exception as e:
                logger.error(f"Error searching WatchSoMuch: {e}")
        
        # Filter results
        filtered_results = self._filter_results(
            results=all_results,
            quality=quality,
            min_size_gb=min_size_gb,
            max_size_gb=max_size_gb
        )
        
        # Remove blacklisted torrents
        filtered_results = [
            r for r in filtered_results
            if r.get('hash') not in self.blacklist
        ]
        
        # Sort by seeds (descending)
        filtered_results.sort(key=lambda x: x.get('seeds', 0), reverse=True)
        
        logger.info(f"Returning {len(filtered_results)} filtered results")
        return filtered_results
    
    def _filter_results(
        self,
        results: List[Dict],
        quality: str,
        min_size_gb: float,
        max_size_gb: float
    ) -> List[Dict]:
        """Filter torrent results based on criteria"""
        filtered = []
        
        for result in results:
            # Check size
            size_gb = result.get('size_gb', 0)
            if size_gb < min_size_gb or size_gb > max_size_gb:
                continue
            
            # Check quality
            if quality:
                quality_keywords = Config.QUALITY_KEYWORDS.get(quality, [])
                if not any(kw.lower() in result.get('name', '').lower()
                          for kw in quality_keywords):
                    continue
            
            # Check for video extensions in name
            name = result.get('name', '').lower()
            has_video_ext = any(
                ext in name for ext in Config.ALLOWED_VIDEO_EXTENSIONS
            )
            
            # If we have file list, check if there are video files
            files = result.get('files', [])
            if files:
                has_video_files = any(
                    any(ext in f.lower() for ext in Config.ALLOWED_VIDEO_EXTENSIONS)
                    for f in files
                )
                if not has_video_files:
                    continue
            
            filtered.append(result)
        
        return filtered
    
    def add_torrent(
        self,
        magnet_link: str,
        source: str = 'unknown',
        name: str = ''
    ) -> Dict:
        """
        Add torrent to qBittorrent
        
        Args:
            magnet_link: Magnet link
            source: Source of torrent
            name: Torrent name
        
        Returns:
            Dict with result information
        """
        try:
            result = self.qb_client.add_torrent(
                magnet_link=magnet_link,
                tags=[source]
            )
            
            if result.get('success'):
                torrent_hash = result.get('hash')
                
                # Add to history
                self._add_to_history({
                    'hash': torrent_hash,
                    'name': name or result.get('name'),
                    'source': source,
                    'added_at': datetime.now().isoformat(),
                    'magnet': magnet_link
                })
                
                # Set file priorities (skip non-video files)
                self._set_file_priorities(torrent_hash)
                
                logger.info(f"Successfully added torrent: {torrent_hash}")
                return result
            
            return result
            
        except Exception as e:
            logger.error(f"Error adding torrent: {e}")
            raise

    def _set_file_priorities(self, torrent_hash: str):
        """Set file priorities to skip non-video files"""
        try:
            time.sleep(2)  # Wait for torrent metadata
            
            files = self.qb_client.get_torrent_files(torrent_hash)
            
            if not files:
                return
            
            skip_files = []
            keep_files = []
            
            for file in files:
                file_name = file.get('name', '').lower()
                file_id = file.get('index')
                
                # Check if file should be skipped
                should_skip = any(
                    ext in file_name for ext in Config.EXCLUDED_EXTENSIONS
                )
                
                # Check if it's a video file
                is_video = any(
                    ext in file_name for ext in Config.ALLOWED_VIDEO_EXTENSIONS
                )
                
                if should_skip and not is_video:
                    skip_files.append(file_id)
                else:
                    keep_files.append(file_id)
            
            # Set priorities
            if skip_files:
                self.qb_client.set_file_priority(
                    torrent_hash=torrent_hash,
                    file_ids=skip_files,
                    priority=0  # Skip
                )
                logger.info(
                    f"Skipping {len(skip_files)} non-video files "
                    f"for torrent {torrent_hash}"
                )
            
        except Exception as e:
            logger.error(f"Error setting file priorities: {e}")
    
    def monitor_and_manage_torrents(self):
        """Monitor torrents and handle stalled/failed downloads"""
        try:
            torrents = self.qb_client.get_all_torrents()
            
            for torrent in torrents:
                torrent_hash = torrent.get('hash')
                state = torrent.get('state', '')
                
                # Check if torrent should be handled
                if self._should_retry_torrent(torrent):
                    logger.warning(
                        f"Torrent {torrent_hash} is stalled/failed, "
                        f"adding to blacklist"
                    )
                    
                    # Add to blacklist
                    self._add_to_blacklist(torrent_hash, torrent.get('name'))
                    
                    # Delete torrent
                    self.qb_client.delete_torrent(torrent_hash, delete_files=False)
                    
                    # Try to find alternative
                    self._find_and_add_alternative(torrent.get('name'))
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
    
    def _should_retry_torrent(self, torrent: Dict) -> bool:
        """Check if a torrent should be retried with alternative"""
        state = torrent.get('state', '').lower()
        dlspeed = torrent.get('dlspeed', 0)
        num_seeds = torrent.get('num_seeds', 0)
        
        # Check for various failure conditions
        if 'error' in state or 'missing' in state:
            return True
        
        # Check if stalled
        if 'stalled' in state and dlspeed == 0:
            return True
        
        # Check if no seeds
        if num_seeds < Config.MIN_SEEDS:
            return True
        
        # Check if download speed too low for too long
        if dlspeed > 0 and dlspeed < Config.MIN_DOWNLOAD_SPEED_KB * 1024:
            # In production, track this over time
            return True
        
        return False
    
    def _find_and_add_alternative(self, original_name: str):
        """Find and add an alternative torrent"""
        try:
            # Search for alternatives
            results = self.search_torrents(
                query=original_name,
                sources=['1337x', 'watchsomuch']
            )
            
            # Filter out blacklisted results
            alternatives = [
                r for r in results
                if r.get('hash') not in self.blacklist
            ]
            
            if alternatives:
                # Get the best alternative (highest seeds)
                best = alternatives[0]
                
                logger.info(
                    f"Found alternative for '{original_name}': "
                    f"{best.get('name')}"
                )
                
                # Add the alternative
                if best.get('magnet_link'):
                    self.add_torrent(
                        magnet_link=best['magnet_link'],
                        source=best.get('source', 'unknown'),
                        name=best.get('name')
                    )
            else:
                logger.warning(
                    f"No alternatives found for '{original_name}'"
                )
                
        except Exception as e:
            logger.error(f"Error finding alternative: {e}")
    
    def get_all_torrents(self) -> List[Dict]:
        """Get all torrents from qBittorrent"""
        return self.qb_client.get_all_torrents()
    
    def get_torrent_info(self, torrent_hash: str) -> Optional[Dict]:
        """Get detailed info about a torrent"""
        return self.qb_client.get_torrent_info(torrent_hash)
    
    def delete_torrent(self, torrent_hash: str, delete_files: bool = False):
        """Delete a torrent"""
        self.qb_client.delete_torrent(torrent_hash, delete_files)
    
    def _load_blacklist(self) -> set:
        """Load blacklist from file"""
        try:
            if self.blacklist_file.exists():
                with open(self.blacklist_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('hashes', []))
            return set()
        except Exception as e:
            logger.error(f"Error loading blacklist: {e}")
            return set()
    
    def _save_blacklist(self):
        """Save blacklist to file"""
        try:
            with open(self.blacklist_file, 'w') as f:
                json.dump({'hashes': list(self.blacklist)}, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving blacklist: {e}")
    
    def _add_to_blacklist(self, torrent_hash: str, name: str = ''):
        """Add torrent to blacklist"""
        self.blacklist.add(torrent_hash)
        self._save_blacklist()
        logger.info(f"Added {torrent_hash} ({name}) to blacklist")
    
    def get_blacklist(self) -> List[str]:
        """Get blacklist"""
        return list(self.blacklist)
    
    def remove_from_blacklist(self, torrent_hash: str):
        """Remove from blacklist"""
        self.blacklist.discard(torrent_hash)
        self._save_blacklist()
    
    def _load_history(self) -> List[Dict]:
        """Load torrent history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return []
    
    def _save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def _add_to_history(self, entry: Dict):
        """Add entry to history"""
        self.history.append(entry)
        self._save_history()