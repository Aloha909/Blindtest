import json
import random


def playlist_order_maker(playlists: list, length: int = 10) -> list:
    liste = []
    random.shuffle(playlists)
    for i in range(length):
        liste.append(playlists[i % len(playlists)])
    random.shuffle(liste)
    return liste


def songs_picker(playlists: list) -> list:
    liste = []
    past = set()
    for playlist in playlists:
        added = False
        while not added:
            data = json.load(open(f"data/playlists/{playlist}.json", 'r', encoding='utf-8'))
            i = random.randint(0, data['length'] - 1)
            if data['tracks'][i]['track_id'] not in past:
                liste.append(data['tracks'][i])
                past.add(data['tracks'][i]['track_id'])
                added = True
    return liste



if __name__ == "__main__":
    years = [2015, 2016, 2017, 2018, 2019]
    y = playlist_order_maker(years, 10)
    songs = songs_picker(y)
    print(songs)
