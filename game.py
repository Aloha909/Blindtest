import datetime
import json
import os

import soco.data_structures
import spotipy
from soco import SoCo

from utils.generator import songs_picker, playlist_order_maker


def save_song_list(playlists: list, nb_songs: int):
    p = playlist_order_maker(playlists, nb_songs)
    songs = songs_picker(p)
    json.dump({'future': songs, 'past': []}, open("current_game/songs.json", "w", encoding="utf-8"), ensure_ascii=False)

def play_song(sp: spotipy.Spotify, song: dict):
    config = json.load(open('current_game/config.json', 'r', encoding='utf-8'))
    delay = min(datetime.datetime.strptime(song['chorus_start'], "%M:%S").time(), datetime.time(0, 0, config['delay'])).second
    start = (datetime.datetime.combine(datetime.date.today(), datetime.datetime.strptime(song['chorus_start'], "%M:%S").time()) - datetime.timedelta(seconds=delay)).time()
    sp.start_playback(uris=[f"spotify:track:{song['track_id']}"],
                      device_id=os.getenv('SPOTIFY_COMPUTER_ID'),
                      position_ms=start.minute * 60000 + start.second * 1000)

def play_on_sonos(speaker: SoCo, song: dict):
    config = json.load(open('current_game/config.json', 'r', encoding='utf-8'))
    delay = min(datetime.datetime.strptime(song['chorus_start'], "%M:%S").time(),datetime.time(0, 0, config['delay'])).second
    start = (datetime.datetime.combine(datetime.date.today(), datetime.datetime.strptime(song['chorus_start'],"%M:%S").time()) - datetime.timedelta(seconds=delay)).time()
    uri = f"x-sonos-spotify:spotify%3atrack%3a{song['track_id']}?sid=9&flags=8224&sn=1"  # ?sid=9&flags=8224&sn=1"
    duration = "0:" + str((song['duration'] * 1000) // 60).zfill(2) + ":" + str(
        round((song['duration'] * 1000) % 60, 0)).zfill(2)
    resources = [soco.data_structures.DidlResource(uri=uri, protocol_info='sonos.com-spotify:*:audio/x-spotify:*',
                                                   duration=duration)]
    song_repr = soco.data_structures.DidlMusicTrack(title='Blindtest...', parent_id='Q:0', item_id='Q:0/2',
                                                    restricted=True, resources=resources, desc=None)
    speaker.add_to_queue(song_repr, 1)
    d = {'position': f"0:{start.strftime('%M:%S')}", 'track': 0}
    speaker.seek(**d)
    speaker.play()
    while speaker.get_current_transport_info()['current_transport_state'] == 'TRANSITIONING' :  # Wait for the song to really start playing
        continue