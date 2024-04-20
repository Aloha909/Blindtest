# Blindtest by [Aloha909](https://github.com/Aloha909)

Blindtest app based on custom playlists.\

### App
To start the app, run the `app.py` file.


### Environment
Install the required packages with `pip install -r requirements.txt`.

Beware, some environment variables are required to run the app : 
- SPOTIFY_CLIENT_ID
- SPOTIFY_CLIENT_SECRET


- GENIUS_CLIENT_ID
- GENIUS_CLIENT_SECRET
- GENIUS_AUTHORIZATION


- SPOTIFY_COMPUTER_ID


- LYRICS_URL


- SONOS_IP

The spotify computer id is the id of the computer that will play the music. It is used to start playback on the computer. The sonos ip is the local ip address of the sonos speaker that will play the music. You can use exclusively one of the two. In that case, pay attention to the `Play on sonos speaker` switch in the `Configuration` page.

The lyrics url is the url of the lyrics server (source code will come soon). 

You have to create a Spotify app on the Spotify developer dashboard to get the client id and client secret.

You also have to create a Genius developper account to get the client id, client secret and authorization token.
