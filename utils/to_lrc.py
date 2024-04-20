import os
from utils import custom_requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def correct_for_file_name(string):
    return string.replace('/', '').replace('\\', '').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')

def download_lrc_file(song):
    artist, title, album, duration = correct_for_file_name(song['artist']), correct_for_file_name(song['title'].split(' (')[0].split(' -')[0]), song[
        'album'], song['duration']
    lyrics_url = os.getenv('LYRICS_URL')
    if os.path.exists(f"{os.getcwd()}/data/lrc/{artist} - {title}.lrc"):
        try:
            print(f"{artist} - {title}.lrc already exists")
        except Exception:
            print('Print error')
    else:
        minutes = int(duration // 60000)
        seconds = int(round((duration % 60000) / 1000, 2))
        millis = int(round((seconds % 1) * 100, 0))
        duration_formatted = f"{str(minutes).zfill(2)}:{str(seconds).zfill(2)}.{str(millis).zfill(2)}"
        string = f"[ti:{title}]\n[al:{album}]\n[ar:{artist}]\n[length: {duration_formatted}]\n"
        data = custom_requests.get(
            f"{lyrics_url}?trackid={song['track_id']}&format=lrc").json()
        try:
            for line in data['lines']:
                string += f"[{line['timeTag']}] {line['words']}\n"
        except KeyError:
            print(f"No lyrics available for {artist} - {title}")

        with open(f"{os.getcwd()}/data/lrc/{artist} - {title}.lrc", "w", encoding='utf-8') as f:
            f.write(string)
            print("\n-------------------\n")
            print(f"Saved {artist} - {title}.lrc")
