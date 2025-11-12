"""
Configuration Module
All configurable settings for the torrent management system
"""

import os


class Config:
    """Configuration class with all system settings"""
    
    # Flask Configuration
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 5000))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
    
    # qBittorrent Configuration
    QBITTORRENT_HOST = os.environ.get('QBITTORRENT_HOST', 'localhost')
    QBITTORRENT_PORT = int(os.environ.get('QBITTORRENT_PORT', 8080))
    QBITTORRENT_USERNAME = os.environ.get('QBITTORRENT_USERNAME', 'admin')
    QBITTORRENT_PASSWORD = os.environ.get('QBITTORRENT_PASSWORD', 'adminadmin')
    
    # Search Configuration
    SEARCH_TIMEOUT = int(os.environ.get('SEARCH_TIMEOUT', 30))
    MAX_SEARCH_RESULTS = int(os.environ.get('MAX_SEARCH_RESULTS', 50))
    USER_AGENT = os.environ.get(
        'USER_AGENT',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    
    # Quality Filters
    QUALITY_KEYWORDS = {
        '720p': ['720p', 'HD', 'HDTV'],
        '1080p': ['1080p', 'FHD', 'Full HD', 'FullHD'],
        '2160p': ['2160p', '4K', 'UHD'],
        '480p': ['480p', 'SD'],
    }
    
    # File Filters
    ALLOWED_VIDEO_EXTENSIONS = ['.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv']
    EXCLUDED_EXTENSIONS = ['.txt', '.nfo', '.jpg', '.png', '.srt', '.sub']
    
    # Size Configuration (in GB)
    DEFAULT_MIN_SIZE = float(os.environ.get('DEFAULT_MIN_SIZE', 0.1))
    DEFAULT_MAX_SIZE = float(os.environ.get('DEFAULT_MAX_SIZE', 50))
    
    # Monitoring Configuration
    MONITORING_INTERVAL = int(os.environ.get('MONITORING_INTERVAL', 60))
    MIN_DOWNLOAD_SPEED_KB = int(os.environ.get('MIN_DOWNLOAD_SPEED_KB', 10))
    MIN_SEEDS = int(os.environ.get('MIN_SEEDS', 1))
    STALLED_TIME_SECONDS = int(os.environ.get('STALLED_TIME_SECONDS', 300))
    MAX_RETRY_ATTEMPTS = int(os.environ.get('MAX_RETRY_ATTEMPTS', 3))
    
    # Download Configuration
    CONTENT_LAYOUT = os.environ.get('CONTENT_LAYOUT', 'Original')
    AUTO_TMM = os.environ.get('AUTO_TMM', 'False').lower() == 'true'
    SEQUENTIAL_DOWNLOAD = os.environ.get('SEQUENTIAL_DOWNLOAD', 'False').lower() == 'true'
    FIRST_LAST_PIECE_PRIO = os.environ.get('FIRST_LAST_PIECE_PRIO', 'False').lower() == 'true'
    
    # Database/Storage Configuration
    BLACKLIST_FILE = os.environ.get('BLACKLIST_FILE', 'blacklist.json')
    TORRENT_HISTORY_FILE = os.environ.get('TORRENT_HISTORY_FILE', 'history.json')
    
    # Scraper Configuration
    ENABLE_1337X = os.environ.get('ENABLE_1337X', 'True').lower() == 'true'
    ENABLE_WATCHSOMUCH = os.environ.get('ENABLE_WATCHSOMUCH', 'True').lower() == 'true'
    
    # 1337x Configuration
    LEETX_BASE_URL = os.environ.get('LEETX_BASE_URL', 'https://1337x.to')
    LEETX_SEARCH_URL = f"{LEETX_BASE_URL}/search/{{}}/1/"
    
    # WatchSoMuch Configuration
    WATCHSOMUCH_BASE_URL = os.environ.get(
        'WATCHSOMUCH_BASE_URL',
        'https://watchsomuch.to'
    )
    
    # Jellyfin Configuration (for future integration)
    JELLYFIN_ENABLED = os.environ.get('JELLYFIN_ENABLED', 'False').lower() == 'true'
    JELLYFIN_URL = os.environ.get('JELLYFIN_URL', 'http://localhost:8096')
    JELLYFIN_API_KEY = os.environ.get('JELLYFIN_API_KEY', '')
    JELLYFIN_LIBRARY_PATHS = os.environ.get('JELLYFIN_LIBRARY_PATHS', '').split(',')
    JELLYFIN_AUTO_SCAN = os.environ.get('JELLYFIN_AUTO_SCAN', 'True').lower() == 'true'
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'torrent_manager.log')
    
    @classmethod
    def validate_config(cls):
        """Validate critical configuration values"""
        errors = []
        
        if not cls.QBITTORRENT_HOST:
            errors.append("QBITTORRENT_HOST is required")
        
        if not cls.QBITTORRENT_USERNAME or not cls.QBITTORRENT_PASSWORD:
            errors.append("qBittorrent credentials are required")
        
        if cls.MONITORING_INTERVAL < 10:
            errors.append("MONITORING_INTERVAL should be at least 10 seconds")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
    

