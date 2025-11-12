"""
Jellyfin Integration Module
Handles automatic library scanning and media organization for Jellyfin
NOTE: This is prepared for future integration - enable when ready
"""

import requests
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class JellyfinClient:
    """Client for Jellyfin API integration"""
    
    def __init__(
        self,
        url: str,
        api_key: str,
        library_paths: List[str] = None
    ):
        """
        Initialize Jellyfin client
        
        Args:
            url: Jellyfin server URL (e.g., http://localhost:8096)
            api_key: Jellyfin API key
            library_paths: List of library paths to scan
        """
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.library_paths = library_paths or []
        self.session = requests.Session()
        self.session.headers.update({
            'X-Emby-Token': api_key,
            'Content-Type': 'application/json'
        })
        
        # Test connection
        if not self._test_connection():
            logger.warning("Failed to connect to Jellyfin server")
    
    def _test_connection(self) -> bool:
        """Test connection to Jellyfin server"""
        try:
            response = self.session.get(
                f"{self.url}/System/Info",
                timeout=10
            )
            
            if response.status_code == 200:
                info = response.json()
                logger.info(
                    f"Connected to Jellyfin {info.get('Version', 'unknown')}"
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to Jellyfin: {e}")
            return False
    
    def get_libraries(self) -> List[Dict]:
        """
        Get all media libraries from Jellyfin
        
        Returns:
            List of library information dicts
        """
        try:
            response = self.session.get(
                f"{self.url}/Library/MediaFolders",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('Items', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting libraries: {e}")
            return []
    
    def scan_library(self, library_id: Optional[str] = None) -> bool:
        """
        Trigger library scan in Jellyfin
        
        Args:
            library_id: Specific library ID to scan (None for all)
        
        Returns:
            True if scan initiated successfully
        """
        try:
            if library_id:
                # Scan specific library
                url = f"{self.url}/Items/{library_id}/Refresh"
                params = {
                    'Recursive': 'true',
                    'ImageRefreshMode': 'Default',
                    'MetadataRefreshMode': 'Default',
                    'ReplaceAllImages': 'false',
                    'ReplaceAllMetadata': 'false'
                }
            else:
                # Scan all libraries
                url = f"{self.url}/Library/Refresh"
                params = {}
            
            response = self.session.post(url, params=params, timeout=30)
            
            if response.status_code in [200, 204]:
                logger.info(
                    f"Library scan initiated "
                    f"({'specific' if library_id else 'all libraries'})"
                )
                return True
            
            logger.warning(f"Library scan failed: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"Error initiating library scan: {e}")
            return False
    
    def find_library_by_path(self, file_path: str) -> Optional[str]:
        """
        Find library ID that contains the given file path
        
        Args:
            file_path: Path to downloaded file
        
        Returns:
            Library ID or None
        """
        try:
            libraries = self.get_libraries()
            file_path = Path(file_path).resolve()
            
            for library in libraries:
                for location in library.get('Locations', []):
                    lib_path = Path(location).resolve()
                    try:
                        # Check if file is under this library path
                        file_path.relative_to(lib_path)
                        return library.get('Id')
                    except ValueError:
                        # Not under this library path
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding library: {e}")
            return None
    
    def scan_for_new_media(self, download_path: str) -> bool:
        """
        Scan Jellyfin libraries for newly downloaded media
        
        Args:
            download_path: Path where media was downloaded
        
        Returns:
            True if scan was successful
        """
        try:
            # Find which library contains this path
            library_id = self.find_library_by_path(download_path)
            
            if library_id:
                logger.info(f"Scanning library {library_id} for new media")
                return self.scan_library(library_id)
            else:
                # Scan all libraries if we can't determine specific one
                logger.info("Scanning all libraries for new media")
                return self.scan_library()
            
        except Exception as e:
            logger.error(f"Error scanning for new media: {e}")
            return False
    
    def get_recently_added(self, limit: int = 10) -> List[Dict]:
        """
        Get recently added items from Jellyfin
        
        Args:
            limit: Maximum number of items to return
        
        Returns:
            List of recently added media items
        """
        try:
            params = {
                'Limit': limit,
                'Recursive': 'true',
                'SortBy': 'DateCreated',
                'SortOrder': 'Descending',
                'IncludeItemTypes': 'Movie,Episode'
            }
            
            response = self.session.get(
                f"{self.url}/Users/{self._get_user_id()}/Items",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('Items', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting recently added: {e}")
            return []
    
    def _get_user_id(self) -> str:
        """Get the first admin user ID"""
        try:
            response = self.session.get(
                f"{self.url}/Users",
                timeout=10
            )
            
            if response.status_code == 200:
                users = response.json()
                # Return first user (usually admin)
                if users:
                    return users[0].get('Id', '')
            
            return ''
            
        except Exception as e:
            logger.error(f"Error getting user ID: {e}")
            return ''


class JellyfinIntegration:
    """High-level Jellyfin integration for torrent manager"""
    
    def __init__(
        self,
        enabled: bool,
        url: str,
        api_key: str,
        library_paths: List[str] = None,
        auto_scan: bool = True
    ):
        """
        Initialize Jellyfin integration
        
        Args:
            enabled: Whether integration is enabled
            url: Jellyfin server URL
            api_key: Jellyfin API key
            library_paths: Library paths to monitor
            auto_scan: Automatically scan after downloads
        """
        self.enabled = enabled
        self.auto_scan = auto_scan
        self.client = None
        
        if enabled and url and api_key:
            try:
                self.client = JellyfinClient(
                    url=url,
                    api_key=api_key,
                    library_paths=library_paths
                )
                logger.info("Jellyfin integration initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Jellyfin: {e}")
                self.enabled = False
    
    def on_download_complete(
        self,
        torrent_hash: str,
        file_path: str,
        torrent_name: str
    ) -> bool:
        """
        Called when a torrent download completes
        
        Args:
            torrent_hash: Torrent hash
            file_path: Path to downloaded files
            torrent_name: Name of torrent
        
        Returns:
            True if Jellyfin was updated successfully
        """
        if not self.enabled or not self.client:
            return False
        
        if not self.auto_scan:
            logger.info("Auto-scan disabled, skipping Jellyfin update")
            return False
        
        try:
            logger.info(
                f"Notifying Jellyfin of new media: {torrent_name}"
            )
            
            # Trigger library scan
            success = self.client.scan_for_new_media(file_path)
            
            if success:
                logger.info(
                    f"Successfully triggered Jellyfin scan for {torrent_name}"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating Jellyfin: {e}")
            return False
    
    def get_status(self) -> Dict:
        """
        Get Jellyfin integration status
        
        Returns:
            Dict with status information
        """
        status = {
            'enabled': self.enabled,
            'auto_scan': self.auto_scan,
            'connected': False,
            'libraries': []
        }
        
        if self.enabled and self.client:
            # Test connection
            status['connected'] = self.client._test_connection()
            
            if status['connected']:
                status['libraries'] = self.client.get_libraries()
        
        return status


# Example usage for future implementation in torrent_manager.py:
"""
from config import Config
from jellyfin_integration import JellyfinIntegration

# Initialize in __init__
self.jellyfin = JellyfinIntegration(
    enabled=Config.JELLYFIN_ENABLED,
    url=Config.JELLYFIN_URL,
    api_key=Config.JELLYFIN_API_KEY,
    library_paths=Config.JELLYFIN_LIBRARY_PATHS,
    auto_scan=Config.JELLYFIN_AUTO_SCAN
)

# Call when download completes in monitor_and_manage_torrents()
if torrent.get('progress') >= 1.0:
    torrent_info = self.qb_client.get_torrent_info(torrent_hash)
    if torrent_info:
        self.jellyfin.on_download_complete(
            torrent_hash=torrent_hash,
            file_path=torrent_info.get('save_path'),
            torrent_name=torrent_info.get('name')
        )
"""