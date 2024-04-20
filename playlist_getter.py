import json
import time
import concurrent.futures
import traceback

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from utils import custom_requests
from utils.genius import get_first_line_of_chorus_and_image, find_time_for_line
from utils.to_lrc import download_lrc_file, correct_for_file_name
from utils.ressources import sp

def load_song_start_and_image(song: dict, delay: int):
    download_lrc_file(song)  # Creates the .lrc file
    start = None
    skips = 0
    song_art = None
    while start is None:
        string, song_art = get_first_line_of_chorus_and_image(song['artist'], song['title'],
                                                    skips)  # Gets the first line of the chorus
        start = find_time_for_line(string,
                                   f"{correct_for_file_name(song['artist'])} - {correct_for_file_name(song['title'].split(' (')[0].split(' -')[0])}.lrc",
                                   delay)  # Finds the start of the chorus
        skips += 1
    return start.strftime("%M:%S"), song_art


def get_playlist_items(sp, plid, name, offset, total, batch_size=100):
    t = time.time()
    custom_requests.get(f"http://127.0.0.1:5000/add-batch/{name}/{int(offset / batch_size)}/{min(total - offset, batch_size)}")
    items = sp.playlist_items(plid, limit=batch_size, offset=offset)
    tracks = []
    counter = 0
    for song in items['items']:
        print(f"Song {counter} of batch {offset // batch_size} - {round(time.time() - t, 2)}s")
        custom_requests.get(f"http://127.0.0.1:5000/update-batch/{name}/{int(offset // batch_size)}/{counter + 1}")
        track = {}
        track['title'] = song['track']['name']
        track['artist'] = song['track']['artists'][0]['name']
        track['album'] = song['track']['album']['name']
        track['track_id'] = song['track']['id']
        track['album'] = song['track']['album']['name']
        track['duration'] = song['track']['duration_ms']
        track['playlist'] = name
        chorus_start, song_art = load_song_start_and_image(track, 0)
        track['chorus_start'] = chorus_start
        track['song_art'] = song_art or "../static/default-img.png"
        tracks.append(track)
        counter += 1
    print(f"Batch {offset // batch_size} done")
    custom_requests.get(f"http://127.0.0.1:5000/finish-batch/{name}/{int(offset / batch_size)}")
    return tracks


def reload_batch(playlist_name, batch_number, batch_size=100):
    data = json.load(open(f"data/playlists/{playlist_name}.json", "r", encoding="utf-8"))
    try :
        data['tracks'].extend(get_playlist_items(sp, data['id'], playlist_name, (int(batch_number)*int(batch_size)), data['length'], int(batch_size)))
        json.dump(data, open(f"data/playlists/{playlist_name}.json", "w", encoding="utf-8"), ensure_ascii=False)
    except Exception as exc:
        print(f"Generated an exception: {exc} at offset: {batch_number}")
        print("details : ")
        print(traceback.format_exc())
        print("-------------------")
        custom_requests.get(f"http://127.0.0.1:5000/fail-batch/{playlist_name}/{int(batch_number)}")

def get_songs_for_playlist(sp, name, plid: str, batch_size=100):
    t = time.time()
    data = {}
    data['name'] = name
    data['id'] = plid
    items = sp.playlist_items(plid, limit=batch_size, offset=0)
    data['length'] = items['total']
    data['tracks'] = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_offset = {
            executor.submit(get_playlist_items, sp, plid, name, offset, items['total'], batch_size): offset for
            offset in range(0, data['length'], batch_size)}
        custom_requests.get(f"http://127.0.0.1:5000/reload-clients")
        for future in concurrent.futures.as_completed(future_to_offset):
            offset = future_to_offset[future]
            try:
                data['tracks'].extend(future.result())
            except Exception as exc:
                print(f"Generated an exception: {exc} at offset: {offset // batch_size}")
                print("details : ")
                print(traceback.format_exc())
                print("-------------------")
                custom_requests.get(f"http://127.0.0.1:5000/fail-batch/{name}/{int(offset // batch_size)}")

    json.dump(data, open(f"data/playlists/{name}.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Added {name} in {time.time() - t}s")
    custom_requests.get(f"http://127.0.0.1:5000/reload-clients")


def get_all_playlists(sp, batch_size=100):
    # check if "data/playlist_ids.json" exists and create it if not
    try:
        playlist_ids = json.load(open("data/playlist_ids.json", 'r', encoding='utf-8'))
    except FileNotFoundError:
        playlist_ids = {'playlists': {}, 'analysed': []}
        json.dump(playlist_ids, open("data/playlist_ids.json", "w", encoding='utf-8'), ensure_ascii=False)
    # Normal code
    for name, plid in playlist_ids['playlists'].items():
        if name not in playlist_ids['analysed']:
            get_songs_for_playlist(sp, name, plid, batch_size)
            playlist_ids['analysed'].append(name)
            json.dump(playlist_ids, open("data/playlist_ids.json", "w", encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    # custom_requests.get(f"http://127.0.0.1:5000/reset")
    # get_songs_for_playlist(sp, "blind_test", "0cY1qx19t14YlfMkbW0HIw", batch_size=15)
    # plids = json.load(open("data/playlist_ids.json", 'r', encoding='utf-8'))
    # name = '1995'
    # get_songs_for_playlist(sp, name, plids[name], batch_size=10)
    get_all_playlists(sp, batch_size=15)
