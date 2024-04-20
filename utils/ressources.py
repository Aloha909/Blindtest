import os
from dotenv import load_dotenv

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from soco import SoCo

# Load environment variables from .env file
load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                                               client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                                               redirect_uri="http://127.0.0.1:8080/",
                                               scope="user-modify-playback-state"))

speaker = SoCo(os.getenv("SONOS_IP"))
