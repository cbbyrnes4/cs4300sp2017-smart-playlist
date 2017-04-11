import django
import requests
import spotipy
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from musixmatch.api import Error, Request
from musixmatch.track import Track
from spotipy.oauth2 import SpotifyClientCredentials

django.setup()

# musixmatch_key = os.environ.get('MUSIXMATCH_KEY')
# spotify_id = os.environ.get('SPOTIFY_ID')
# spotify_secret = os.environ.get('SPOTIFY_SECRET')

musixmatch_key = 'f8192e15050fe5f070871e35d35251a2'
spotify_id = 'd305abf923f54ff0b2bee3ae17af289d'
spotify_secret = '55b73d4d03a44a309973c0693edbeaf9'

spo_cred_manager = SpotifyClientCredentials(spotify_id, spotify_secret)
sp = spotipy.Spotify(client_credentials_manager=spo_cred_manager)

from smart_playlist.models import Song, Artist, Lyric, Album, AudioFeatures


def search_mxm_for_info(mxm_id):
    """
    Searches the MusixMatch Database and creates a song object if one doesn't
    already exist for the mxm_id
    """
    song_match = Song.objects.filter(mxm_tid=mxm_id)
    if not song_match.exists():
        try:
            track = Track(track_id=mxm_id, apikey=musixmatch_key)
            artist, _ = Artist.objects.get_or_create(
                name=track['artist_name'],
                mxm_id=track['artist_id']
            )
            album, _ = Album.objects.get_or_create(
                name=track['album_name'],
                mxm_id=track['album_id'],
                artist=artist
            )
            song = Song.objects.create(name=track['track_name'], album=album, mxm_tid=mxm_id)
            song.save()
            song.artist.add(artist)
            print("Added new song %s" % track['track_name'])
            return True, song
        except Error as e:
            print("Unable to find track with id %d" % mxm_id)
            return False, None
    return True, song_match[0]


def get_song_from_mxm():
    """
    Searches through all of the Lyrics in the database and creates song objects for all those not found
    :return: None
    """
    mxm_ids = Lyric.objects.values('mxm_id').distinct()

    print("Found %d songs" % mxm_ids.count())
    miss_count = 0
    for mxm_id in mxm_ids:
        mxm_id = mxm_id['mxm_id']
        found, song = search_mxm_for_info(mxm_id)
        if not found:
            miss_count += 1
        else:
            if song.spotify_id is None:
                spotify_song_id = search_for_spotify_id(song.name, song.artist.name, song.album.name)
                if spotify_song_id:
                    song.spotify_id = spotify_song_id
                    song.save()
                else:
                    song.delete()

    print("Created %d songs in database" % mxm_ids.count())
    print("Couldn't find %d songs" % miss_count)

    for lyric in Lyric.objects.all():
        try:
            song = Song.objects.get(mxm_id=lyric.mxm_id)
            lyric.song = song
        except ObjectDoesNotExist:
            lyric.delete()
            print("Deleted Lyric with no Musixmatch match")

    print("Updated %d lyrics" % Lyric.objects.all().count())


def search_for_spotify_id(name, artist_name, album_name=None):
    """
    Returns the Spotify ID for a given song name, artist name and album name
    :param name: Name of song to search for (str)
    :param artist_name: Name of artist of song (str)
    :param album_name: Optional name of album of song (str)
    :return: Spotify ID of song
    """
    spo_id, _, _ = get_all_spotify_info(name, artist_name, album_name)
    return spo_id


def get_all_spotify_info(name, artist_name, album_name=None):
    q_string = "track:" + name + " artist:" + artist_name
    if album_name:
        q_string += " album:" + album_name
    try:
        results = sp.search(q=q_string, type='track', limit=1)
        results = results['tracks']['items'][0]
        artists = results['artists']
        artist_info = [(a['name'], a['id']) for a in artists]
        album_info = (results['album']['name'], results['album']['id'])
        song_info = (results['name'], results['id'])
        return song_info, artist_info, album_info
    except KeyError:
        # No Song was found
        return None


def get_mxm_id(name, artist_name):
    song_id, _, _ = get_all_mxm_info(name, artist_name)
    return song_id


def get_all_mxm_info(name, artist_name):
    query_string = 'matcher.track.get'
    keywords = {'q_artist': artist_name, 'q_track': name, 'apikey': musixmatch_key}
    response = requests.get(str(Request(query_string, keywords))).json()
    response = response['message']['body']['track']
    artist_id = response['artist_id']
    art_name = response['artist_name']
    album_id = response['album_id']
    song_id = response['track_id']
    return song_id, (art_name, artist_id), album_id


def build_song(name, artist_name):
    spo_song_info, spo_artist_info, spo_album_info = get_all_spotify_info(name, artist_name)
    if Song.objects.filter(spotify_id=spo_song_info[1]).exists():
        # Song Already Exists
        print("Song Exists")
        return
    mxm_song_id, (mxm_artist_name, mxm_artist_id), mxm_album_id = get_all_mxm_info(name, artist_name)
    print(spo_song_info, spo_artist_info, spo_album_info, mxm_song_id, mxm_artist_name, mxm_artist_id, mxm_album_id)
    artists = []
    for sp_artist_name, artist_spo_id in spo_artist_info:
        if Artist.objects.filter(spotify_id=artist_spo_id).exists():
            artists.append(Artist.objects.get(spotify_id=artist_spo_id))
        else:
            artist = Artist.objects.create(name=sp_artist_name)
            artist.spotify_id = artist_spo_id
            if mxm_artist_name == sp_artist_name:
                artist.mxm_id = mxm_artist_id
            artist.save()
            artists.append(artist)
    print("%d artists" % len(artists))
    if Album.objects.filter(spotify_id=spo_album_info[1]).exists():
        album = Album.objects.get(spotify_id=spo_album_info[1])
    else:
        album = Album.objects.create(name=spo_album_info[0], artist=artists[0])
        album.spotify_id = spo_album_info[1]
        album.mxm_id = mxm_album_id
        album.save()
    song = Song.objects.create(name=spo_song_info[0], spotify_id=spo_song_info[1], mxm_tid=mxm_song_id, album=album)
    song.save()
    for artist in artists:
        song.artist.add(artist)
    get_audio_features([song])
    return song


def get_artists(artist_ids):
    filter_q = Q()
    for a_id in artist_ids:
        filter_q = filter_q | Q(spotify_id=a_id)
    return Artist.objects.filter(filter_q)


def mxm_search_lyrics(name, artist_name):
    mxm_id = get_mxm_id(name, artist_name)
    return mxm_get_lyrics(mxm_id)


def mxm_get_lyrics(mxm_id):
    query_string = 'track.lyrics.get'
    keywords = {'track_id': mxm_id, 'apikey': musixmatch_key}
    response = requests.get(str(Request(query_string, keywords))).json()
    lyrics = response['message']['body']['lyrics']['lyrics_body']
    return lyrics[:lyrics.find('*')]


def get_audio_features(songs):
    song_ids = []
    for song in songs:
        if not song.spotify_id:
            song.spotify_id = search_for_spotify_id(song.name, song.artist.all()[0].name, song.album.name)
        spo_id = song.spotify_id
        song_ids.append((song, spo_id))
    features = sp.audio_features(tracks=[sp_id for song, sp_id in song_ids])
    for i in range(len(song_ids)):
        create_audio_features(song_ids[i][0], features[i])


def create_audio_features(song, features):
    af = AudioFeatures.objects.create(
        song=song,
        acousticness=features['acousticness'],
        danceability=features['danceability'],
        duration_ms=features['duration_ms'],
        energy=features['energy'],
        instrumentalness=features['instrumentalness'],
        key=features['key'],
        liveness=features['liveness'],
        loudness=features['loudness'],
        mode=features['mode'],
        speechiness=features['speechiness'],
        tempo=features['tempo'],
        time_signature=features['time_signature'],
        valence=features['valence']
    )
    af.save()
