"""
Torrent Management System - Main Flask Application
Modular system for searching, downloading, and managing torrents
"""

from flask import Flask, render_template, request, jsonify
from config import Config
from torrent_manager import TorrentManager
import threading
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize torrent manager
torrent_manager = TorrentManager(
    qb_host=Config.QBITTORRENT_HOST,
    qb_port=Config.QBITTORRENT_PORT,
    qb_username=Config.QBITTORRENT_USERNAME,
    qb_password=Config.QBITTORRENT_PASSWORD
)

# Global monitoring thread
monitoring_thread = None
monitoring_active = False


@app.route('/')
def index():
    """Main page with search interface"""
    return render_template('index.html')


@app.route('/api/search', methods=['POST'])
def search_torrents():
    """Search for torrents across multiple sources"""
    try:
        data = request.json
        query = data.get('query', '')
        quality = data.get('quality', '')
        min_size = data.get('min_size', 0)
        max_size = data.get('max_size', float('inf'))
        sources = data.get('sources', ['1337x', 'watchsomuch'])
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        results = torrent_manager.search_torrents(
            query=query,
            quality=quality,
            min_size_gb=min_size,
            max_size_gb=max_size,
            sources=sources
        )
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
def download_torrent():
    """Add torrent to qBittorrent"""
    try:
        data = request.json
        magnet_link = data.get('magnet_link')
        source = data.get('source', 'unknown')
        torrent_name = data.get('name', '')
        
        if not magnet_link:
            return jsonify({'error': 'Magnet link is required'}), 400
        
        result = torrent_manager.add_torrent(
            magnet_link=magnet_link,
            source=source,
            name=torrent_name
        )
        
        return jsonify({
            'success': True,
            'hash': result.get('hash'),
            'message': 'Torrent added successfully'
        })
    
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/torrents', methods=['GET'])
def get_torrents():
    """Get all active torrents"""
    try:
        torrents = torrent_manager.get_all_torrents()
        return jsonify({
            'success': True,
            'torrents': torrents
        })
    
    except Exception as e:
        logger.error(f"Error getting torrents: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/torrent/<hash_id>', methods=['GET'])
def get_torrent_info(hash_id):
    """Get detailed info about a specific torrent"""
    try:
        info = torrent_manager.get_torrent_info(hash_id)
        return jsonify({
            'success': True,
            'torrent': info
        })
    
    except Exception as e:
        logger.error(f"Error getting torrent info: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/torrent/<hash_id>', methods=['DELETE'])
def delete_torrent(hash_id):
    """Delete a torrent"""
    try:
        delete_files = request.args.get('delete_files', 'false').lower() == 'true'
        torrent_manager.delete_torrent(hash_id, delete_files)
        return jsonify({
            'success': True,
            'message': 'Torrent deleted successfully'
        })
    
    except Exception as e:
        logger.error(f"Error deleting torrent: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start automatic torrent monitoring"""
    global monitoring_thread, monitoring_active
    
    try:
        if monitoring_active:
            return jsonify({'message': 'Monitoring already active'}), 200
        
        monitoring_active = True
        monitoring_thread = threading.Thread(
            target=monitor_torrents_loop,
            daemon=True
        )
        monitoring_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Monitoring started'
        })
    
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Stop automatic torrent monitoring"""
    global monitoring_active
    
    try:
        monitoring_active = False
        return jsonify({
            'success': True,
            'message': 'Monitoring stopped'
        })
    
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/monitoring/status', methods=['GET'])
def monitoring_status():
    """Get monitoring status"""
    return jsonify({
        'success': True,
        'active': monitoring_active
    })


@app.route('/api/blacklist', methods=['GET'])
def get_blacklist():
    """Get blacklisted torrents"""
    try:
        blacklist = torrent_manager.get_blacklist()
        return jsonify({
            'success': True,
            'blacklist': blacklist
        })
    
    except Exception as e:
        logger.error(f"Error getting blacklist: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/blacklist/<hash_id>', methods=['DELETE'])
def remove_from_blacklist(hash_id):
    """Remove a torrent from blacklist"""
    try:
        torrent_manager.remove_from_blacklist(hash_id)
        return jsonify({
            'success': True,
            'message': 'Removed from blacklist'
        })
    
    except Exception as e:
        logger.error(f"Error removing from blacklist: {e}")
        return jsonify({'error': str(e)}), 500


def monitor_torrents_loop():
    """Background loop for monitoring torrents"""
    import time
    
    while monitoring_active:
        try:
            torrent_manager.monitor_and_manage_torrents()
            time.sleep(Config.MONITORING_INTERVAL)
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            time.sleep(Config.MONITORING_INTERVAL)


if __name__ == '__main__':
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.DEBUG
    )