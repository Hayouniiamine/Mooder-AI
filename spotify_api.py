import os
import logging
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Spotify API Credentials
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

# Initialize Spotify API Client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

# Public playlists for each mood
MOOD_PLAYLISTS = {
    'happy': '37i9dQZF1DXdPec7aLTmlC',   # Happy Hits!
    'sad': '37i9dQZF1DX7qK8ma5wgG1',     # Life Sucks
    'angry': '37i9dQZF1DX1X7WV84927n',   # Rock Hard
    'neutral': '37i9dQZF1DWU13kKnk03AP'  # Chill Vibes
}

def get_playlist_for_mood(mood):
    """
    Get the Spotify playlist ID for the given mood.
    If mood is not found, return the neutral playlist ID.
    """
    return MOOD_PLAYLISTS.get(mood, MOOD_PLAYLISTS['neutral'])

def fetch_spotify_playlist_info(mood):
    """
    Fetch playlist data from Spotify for the given mood.
    Returns playlist information or None if not found.
    """
    playlist_id = get_playlist_for_mood(mood)
    try:
        playlist_info = sp.playlist(playlist_id, market="US")  # Fetch playlist info
        logger.info(f"Successfully retrieved playlist '{playlist_info['name']}' for mood '{mood}'.")
        return playlist_info
    except SpotifyException as e:
        if e.http_status == 404:
            logger.error(f"Spotify 404 Error: Playlist ID {playlist_id} not found.")
        else:
            logger.error(f"Spotify API Error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None

# Example test
if __name__ == "__main__":
    test_mood = "happy"  # Change this to test other moods
    playlist_info = fetch_spotify_playlist_info(test_mood)
    if playlist_info:
        print(f"Playlist Name: {playlist_info['name']}")
    else:
        print("Failed to fetch playlist.")
