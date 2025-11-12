"""
qBittorrent Client Module
Handles all interactions with qBittorrent Web API
"""

import qbittorrentapi
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class QBittorrentClient:
    """Wrapper for qBittorrent API operations"""
    
    def __init__(self, host: str, port: int, username: str, password: str):
        """
        Initialize qBittorrent client
        
        Args:
            host: qBittorrent host address
            port: qBittorrent port
            username: qBittorrent username
            password: qBittorrent password
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish connection to qBittorrent"""
        try:
            self.client = qbittorrentapi.Client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password
            )
            
            # Test connection
            self.client.auth_log_in()
            logger.info(f"Connected to qBittorrent {self.client.app.version}")
            
        except qbittorrentapi.LoginFailed as e:
            logger.error(f"qBittorrent login failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to qBittorrent: {e}")
            raise
    
    def add_torrent(
        self,
        magnet_link: str,
        save_path: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Dict:
        """
        Add a torrent to qBittorrent
        
        Args:
            magnet_link: Magnet link or torrent URL
            save_path: Download path
            category: Torrent category
            tags: List of tags
            **kwargs: Additional qBittorrent options
        
        Returns:
            Dict with torrent hash and status
        """
        try:
            # Prepare options
            options = {
                'urls': magnet_link,
                'is_paused': False,
            }
            
            if save_path:
                options['savepath'] = save_path
            
            if category:
                options['category'] = category
            
            if tags:
                options['tags'] = ','.join(tags)
            
            # Merge with additional options
            options.update(kwargs)
            
            # Add torrent
            result = self.client.torrents_add(**options)
            
            if result == 'Ok.':
                # Get the torrent hash (we'll need to search for it)
                # Since we just added it, get the most recent torrent
                torrents = self.client.torrents_info()
                if torrents:
                    latest = sorted(
                        torrents,
                        key=lambda t: t.added_on,
                        reverse=True
                    )[0]
                    logger.info(f"Torrent added: {latest.name} ({latest.hash})")
                    return {
                        'success': True,
                        'hash': latest.hash,
                        'name': latest.name
                    }
            
            return {'success': False, 'error': 'Failed to add torrent'}
            
        except Exception as e:
            logger.error(f"Error adding torrent: {e}")
            raise
    
    def get_torrent_info(self, torrent_hash: str) -> Optional[Dict]:
        """
        Get detailed information about a torrent
        
        Args:
            torrent_hash: Torrent hash
        
        Returns:
            Dict with torrent information
        """
        try:
            torrent = self.client.torrents_info(torrent_hashes=torrent_hash)
            
            if not torrent:
                return None
            
            t = torrent[0]
            return {
                'hash': t.hash,
                'name': t.name,
                'size': t.size,
                'progress': t.progress,
                'dlspeed': t.dlspeed,
                'upspeed': t.upspeed,
                'downloaded': t.downloaded,
                'uploaded': t.uploaded,
                'eta': t.eta,
                'state': t.state,
                'num_seeds': t.num_seeds,
                'num_leechs': t.num_leechs,
                'ratio': t.ratio,
                'save_path': t.save_path,
                'category': t.category,
                'tags': t.tags,
                'added_on': t.added_on,
                'completion_on': t.completion_on,
            }
            
        except Exception as e:
            logger.error(f"Error getting torrent info: {e}")
            return None
    
    def get_all_torrents(self) -> List[Dict]:
        """
        Get list of all torrents
        
        Returns:
            List of torrent information dicts
        """
        try:
            torrents = self.client.torrents_info()
            return [
                {
                    'hash': t.hash,
                    'name': t.name,
                    'size': t.size,
                    'progress': t.progress,
                    'dlspeed': t.dlspeed,
                    'state': t.state,
                    'num_seeds': t.num_seeds,
                    'num_leechs': t.num_leechs,
                    'eta': t.eta,
                }
                for t in torrents
            ]
            
        except Exception as e:
            logger.error(f"Error getting all torrents: {e}")
            return []
    
    def get_torrent_files(self, torrent_hash: str) -> List[Dict]:
        """
        Get files in a torrent
        
        Args:
            torrent_hash: Torrent hash
        
        Returns:
            List of files with details
        """
        try:
            files = self.client.torrents_files(torrent_hash=torrent_hash)
            return [
                {
                    'name': f.name,
                    'size': f.size,
                    'progress': f.progress,
                    'priority': f.priority,
                    'index': f.index,
                }
                for f in files
            ]
            
        except Exception as e:
            logger.error(f"Error getting torrent files: {e}")
            return []
    
    def set_file_priority(
        self,
        torrent_hash: str,
        file_ids: List[int],
        priority: int
    ):
        """
        Set priority for specific files
        
        Args:
            torrent_hash: Torrent hash
            file_ids: List of file IDs
            priority: Priority (0=skip, 1=normal, 6=high, 7=maximal)
        """
        try:
            self.client.torrents_file_priority(
                torrent_hash=torrent_hash,
                file_ids=file_ids,
                priority=priority
            )
            logger.info(f"Set file priority for torrent {torrent_hash}")
            
        except Exception as e:
            logger.error(f"Error setting file priority: {e}")
            raise
    
    def pause_torrent(self, torrent_hash: str):
        """Pause a torrent"""
        try:
            self.client.torrents_pause(torrent_hashes=torrent_hash)
            logger.info(f"Paused torrent: {torrent_hash}")
            
        except Exception as e:
            logger.error(f"Error pausing torrent: {e}")
            raise
    
    def resume_torrent(self, torrent_hash: str):
        """Resume a torrent"""
        try:
            self.client.torrents_resume(torrent_hashes=torrent_hash)
            logger.info(f"Resumed torrent: {torrent_hash}")
            
        except Exception as e:
            logger.error(f"Error resuming torrent: {e}")
            raise
    
    def delete_torrent(self, torrent_hash: str, delete_files: bool = False):
        """
        Delete a torrent
        
        Args:
            torrent_hash: Torrent hash
            delete_files: Whether to delete downloaded files
        """
        try:
            self.client.torrents_delete(
                torrent_hashes=torrent_hash,
                delete_files=delete_files
            )
            logger.info(
                f"Deleted torrent: {torrent_hash} "
                f"(files={'deleted' if delete_files else 'kept'})"
            )
            
        except Exception as e:
            logger.error(f"Error deleting torrent: {e}")
            raise
    
    def recheck_torrent(self, torrent_hash: str):
        """Force recheck of torrent"""
        try:
            self.client.torrents_recheck(torrent_hashes=torrent_hash)
            logger.info(f"Rechecking torrent: {torrent_hash}")
            
        except Exception as e:
            logger.error(f"Error rechecking torrent: {e}")
            raise