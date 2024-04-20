from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO
from playlist_getter import sp, reload_batch, get_all_playlists, get_songs_for_playlist
import json
from app import app, socketio

if __name__ == '__main__':
    app = Flask(__name__)
    socketio = SocketIO(app)

progress = {}


@app.route('/playlists')
def playlists():
    playlists = get_playlists()
    analysed_playlists = get_analysed_playlists()
    unanalysed_playlists = any(playlist not in analysed_playlists for playlist in playlists)
    return render_template('playlists.html', playlists=playlists, analysed_playlists=analysed_playlists, unanalysed_playlists=unanalysed_playlists)

@app.route('/add-playlist', methods=['POST'])
def add_playlist():
    data = request.get_json()
    name = data['playlistName']
    playlist = data['spotifyId']

    if 'open.spotify.com/playlist' in playlist:
        plid = playlist.split('playlist/')[1].split('?')[0]
    elif 'open.spotify.com' in playlist:
        return 'Not a valid Spotify URL', 500
    else :
        plid = playlist
    try :
        playlist_ids: dict = json.load(open("data/playlist_ids.json", 'r', encoding='utf-8'))
    except FileNotFoundError:
        playlist_ids = {'playlists': {}, 'analysed': []}
        json.dump(playlist_ids, open("data/playlist_ids.json", "w", encoding='utf-8'), ensure_ascii=False)
    if name not in playlist_ids['playlists'] and plid not in playlist_ids['playlists'].values():
        playlist_ids['playlists'][name] = plid
        json.dump(playlist_ids, open("data/playlist_ids.json", "w", encoding='utf-8'), ensure_ascii=False)
        socketio.emit('playlist_added', {'playlist': name})
        return f"Playlist {name} has been added", 200
    elif name not in playlist_ids:
        return f"This playlist ID is already saved under the name : {[key for key, value in playlist_ids['playlists'].items() if value == name][0]}"
    else:
        return f"Playlist {name} is already saved"

@app.route('/get-playlists')
def get_playlists():
    try:
        playlist_ids = json.load(open("data/playlist_ids.json", 'r', encoding='utf-8'))
    except FileNotFoundError:
        playlist_ids = {'playlists': {}, 'analysed': []}
        json.dump(playlist_ids, open("data/playlist_ids.json", "w", encoding='utf-8'), ensure_ascii=False)
    return list(playlist_ids['playlists'].keys())

@app.route('/get-analysed-playlists')
def get_analysed_playlists():
    try:
        playlist_ids = json.load(open("data/playlist_ids.json", 'r', encoding='utf-8'))
    except FileNotFoundError:
        playlist_ids = {'playlists': {}, 'analysed': []}
        json.dump(playlist_ids, open("data/playlist_ids.json", "w", encoding='utf-8'), ensure_ascii=False)
    return playlist_ids['analysed']

@app.route('/analyse-playlists', methods=['POST'])
def analyse_playlist():
    data = request.get_json()
    batch_size = int(data['batchSize'])
    get_all_playlists(sp, batch_size)
    return redirect('/progress', 303)

@app.route('/progress')
def display_progress():
    active_batches = {}
    finished_batches = {}

    for playlist, batches in progress.items():
        active_batches[playlist] = {}
        finished_batches[playlist] = {}

        for batch, info in batches.items():
            if info['status'] != 'finished':
                active_batches[playlist][batch] = info
            else:
                finished_batches[playlist][batch] = info

    return render_template('progress.html', progress=progress, active_batches=active_batches,
                           finished_batches=finished_batches)


@app.route('/get-progress/<string:playlist>/<int:batch>')
def get_progress(playlist, batch):
    if playlist in progress and batch in progress[playlist]:
        return progress[playlist][batch]
    else:
        return f"No batch found with ID {batch} in playlist {playlist}"


@app.route('/reload-batch', methods=['POST'])
def reload():
    playlist_name = request.form.get('playlistName')
    batch_number = request.form.get('batchNumber')
    batch_size = request.form.get('batchSize')
    # Call your function to reload the batch here
    reload_batch(playlist_name, batch_number, batch_size)
    return 'Batch reloaded', 200


@app.route('/add-batch/<string:playlist>/<int:batch>/<int:batch_size>')
def add_batch(playlist, batch, batch_size):
    if playlist not in progress:
        progress[playlist] = {}
    progress[playlist][batch] = {'value': 0, 'max': batch_size, 'status': 'active'}
    return f"Batch {batch} of playlist {playlist} initialized with progress 0"


@app.route('/update-batch/<string:playlist>/<int:batch>/<int:value>')
def update_batch(playlist, batch, value):
    if playlist in progress and batch in progress[playlist]:
        progress[playlist][batch]['value'] = value
        socketio.emit('progress_update', {'playlist': playlist, 'batch': batch, 'value': value})
        return f"Batch {batch} of playlist {playlist} updated with value {value}"
    else:
        return f"No batch found with ID {batch} in playlist {playlist}"


@app.route('/finish-batch/<string:playlist>/<int:batch>')
def finish_batch(playlist, batch):
    if playlist in progress and batch in progress[playlist]:
        progress[playlist][batch]['value'] = progress[playlist][batch]['max']
        progress[playlist][batch]['status'] = 'finished'
        socketio.emit('batch_finished', {'playlist': playlist, 'batch': batch, 'value': progress[playlist][batch]['value']})
        return f"Batch {batch} of playlist {playlist} is done"
    else:
        return f"No batch found with ID {batch} in playlist {playlist}"


@app.route('/fail-batch/<string:playlist>/<int:batch>')
def fail_batch(playlist, batch):
    if playlist in progress and batch in progress[playlist]:
        progress[playlist][batch]['status'] = 'failed'
        socketio.emit('batch_failed', {'playlist': playlist, 'batch': batch, 'value': progress[playlist][batch]['value']})
        return f"Batch {batch} of playlist {playlist} has failed"
    else:
        return f"No batch found with ID {batch} in playlist {playlist}"


@app.route('/reset')
def reset():
    progress.clear()
    return "All batches have been deleted"


@app.route('/reload-clients')
def reload_clients():
    socketio.emit('reload', {})
    return "Clients have been reloaded"
