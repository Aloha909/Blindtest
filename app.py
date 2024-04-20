from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO
import json
from utils.ressources import sp, speaker
from game import save_song_list, play_song, play_on_sonos
from flask import jsonify
import threading

app = Flask(__name__)
socketio = SocketIO(app)
socketio.emit("reload", {})

import playlist_loader_gui


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mobile')
def mobile():
    return render_template('mobile.html')

@app.route('/pc')
def computer():
    return render_template('computer.html')

@app.route('/test')
def test_mobile():
    return render_template('test_mobile.html')

@socketio.on('pressed')
def button_pressed(data):
    print(data['team'])
    socketio.emit("winner", data)

@socketio.on('reset')
def reset(data):
    socketio.emit("reset", data)

@app.route('/config')
def configuration():
    return render_template('config.html')


@app.route('/save-config', methods=['POST'])
def save_config():
    data = request.get_json()
    playlists = data['playlists']
    nb_songs = int(data['numSongs'])
    delay = int(data['waitTime'])
    sonos = data['playbackToggle']
    json.dump({"playlists": playlists, "nb_songs": nb_songs, "delay": delay, "sonos": sonos},
              open('current_game/config.json', 'w'), ensure_ascii=False)

    return 'Config saved', 204


@app.route('/play')
def start_game():
    try:
        config = json.load(open('current_game/config.json', 'r', encoding='utf-8'))
        save_song_list(config['playlists'], config['nb_songs'])
        return render_template('game.html', initial_time=config['delay'])
    except FileNotFoundError:
        return redirect('/config')


@app.route('/next-song')
def next_song():
    config = json.load(open('current_game/config.json', 'r', encoding='utf-8'))
    with open('current_game/songs.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        songs = data['future']
        past = data['past']
    if not songs:
        return jsonify({'error': 'No more songs'}), 404
    song = songs.pop(0)
    past.append(song)

    if config['sonos']:
        play_on_sonos(speaker, song)
    else:
        play_song(sp, song)

    with open('current_game/songs.json', 'w', encoding='utf-8') as f:
        json.dump({'future': songs, 'past': past}, f, ensure_ascii=False)
    # Start a timer
    threading.Timer(config['delay'], lambda: socketio.emit('songInfo', song)).start()
    return jsonify(song)


@app.route('/recap')
def recap():
    with open('current_game/songs.json', 'r', encoding='utf-8') as f:
        past = json.load(f)['past']
    return render_template('recap.html', songs=past)
