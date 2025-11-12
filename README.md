# 🎬 Advanced Torrent Management System

A comprehensive, modular torrent management system built with Flask and Python. Features automated monitoring, intelligent retry logic, quality filtering, and multi-source torrent searching.

## ✨ Features

- **Multi-Source Search**: Search torrents from 1337x.to and WatchSoMuch.to (public access)
- **Quality Filtering**: Filter by resolution (720p, 1080p, 4K)
- **Size Filtering**: Set minimum and maximum file sizes
- **File Type Filtering**: Automatically skip non-video files
- **Automated Monitoring**: Auto-detect stalled/failed torrents
- **Intelligent Retry**: Automatically find and download alternatives
- **Blacklist Management**: Track failed torrents to avoid re-downloading
- **Web Interface**: Modern, responsive UI for easy management
- **qBittorrent Integration**: Full API integration with qBittorrent
- **Jellyfin Ready**: Prepared for Jellyfin integration (coming soon)

## 📋 Prerequisites

- Python 3.8 or higher
- qBittorrent with Web UI enabled
- Internet connection for torrent searching

## 🚀 Quick Installation

### 1. Install Dependencies
```bash
pip install Flask qbittorrent-api requests beautifulsoup4 lxml python-dotenv
```

### 2. Configure qBittorrent

1. Open qBittorrent → Tools → Options → Web UI
2. Enable "Web User Interface (Remote control)"
3. Set username: `admin` and password: `adminadmin`
4. Port: `8080` (default)

### 3. Create .env File

Copy the `.env` file above and update with your qBittorrent credentials.

### 4. Run the Application
```bash
python app.py
```

Visit: **http://localhost:5000**

## 📁 Project Structure
```
torrent-manager/
├── app.py                      # Main Flask application
├── config.py                   # Configuration module
├── qbittorrent_client.py       # qBittorrent API client
├── scraper_1337x.py           # 1337x scraper (public)
├── scraper_watchsomuch.py     # WatchSoMuch scraper (public)
├── torrent_manager.py         # Core orchestration layer
├── jellyfin_integration.py    # Jellyfin module (ready for future)
├── templates/
│   └── index.html             # Web interface
├── requirements.txt           # Python dependencies
├── .env                       # Environment configuration
├── blacklist.json            # Auto-generated blacklist
└── history.json              # Auto-generated history
```

## 🎯 Usage

### Search for Torrents
1. Enter search query (movie/show name)
2. Select quality (optional)
3. Set size filters (optional)
4. Choose sources (1337x, WatchSoMuch)
5. Click "Search"

### Download & Monitor
1. Click "Download" on desired torrent
2. System automatically adds to qBittorrent
3. Non-video files are automatically skipped
4. Click "Start Monitoring" for automatic management

### Automatic Features
- Detects stalled/failed torrents
- Blacklists problematic torrents
- Finds and downloads alternatives
- Monitors every 60 seconds (configurable)

## 🎬 Jellyfin Integration (Ready When You Are)

The system includes a complete Jellyfin integration module that's ready to activate:

### What's Already Built:
- Automatic library scanning after downloads
- Smart library detection
- Connection health checks
- Recently added media tracking

### To Enable:
1. Install Jellyfin server
2. Generate API key in Jellyfin Dashboard
3. Update `.env`:
```bash
   JELLYFIN_ENABLED=True
   JELLYFIN_URL=http://localhost:8096
   JELLYFIN_API_KEY=your_api_key_here
```
4. See `jellyfin_integration.py` for implementation details

## ⚙️ Configuration

All settings are in `.env`:
```bash
# qBittorrent Settings
QBITTORRENT_HOST=localhost
QBITTORRENT_PORT=8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=adminadmin

# Monitoring
MONITORING_INTERVAL=60
MIN_SEEDS=1
MIN_DOWNLOAD_SPEED_KB=10

# Size Limits
DEFAULT_MIN_SIZE=0.1
DEFAULT_MAX_SIZE=50
```

## 🔧 API Endpoints
```bash
# Search
POST /api/search
Body: {"query": "movie name", "quality": "1080p", "sources": ["1337x"]}

# Download
POST /api/download
Body: {"magnet_link": "magnet:?...", "source": "1337x"}

# Get Torrents
GET /api/torrents

# Start Monitoring
POST /api/monitoring/start

# Stop Monitoring
POST /api/monitoring/stop
```

## 🐛 Troubleshooting

### Can't Connect to qBittorrent
```bash
# Test connection
curl http://localhost:8080/api/v2/app/version -u admin:adminadmin
```

### No Search Results
- Check internet connection
- Try different search terms
- Verify sites are accessible

### Import Errors
```bash
pip install -r requirements.txt
```

## 📝 License

This project is for educational purposes. Users are responsible for complying with local laws regarding torrenting.

## 🚀 Future Features

- Plex integration
- More torrent sources
- Subtitle auto-download
- Notification system (Discord, Telegram)
- Statistics dashboard

---

**Ready to start!** 🎉