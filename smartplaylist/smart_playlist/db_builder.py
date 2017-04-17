import collections

import django
import nltk
import requests
import spotipy
from django.core.exceptions import ObjectDoesNotExist
from musixmatch.api import Error, Request
from musixmatch.track import Track
from spotipy import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from unidecode import unidecode

django.setup()

# musixmatch_key = os.environ.get('MUSIXMATCH_KEY')
# spotify_id = os.environ.get('SPOTIFY_ID')
# spotify_secret = os.environ.get('SPOTIFY_SECRET')

musixmatch_key = 'f8192e15050fe5f070871e35d35251a2'
spotify_key = 'd305abf923f54ff0b2bee3ae17af289d'
spotify_secret = '55b73d4d03a44a309973c0693edbeaf9'

spo_cred_manager = SpotifyClientCredentials(spotify_key, spotify_secret)
sp = spotipy.Spotify(client_credentials_manager=spo_cred_manager)

from smart_playlist.models import Song, Artist, Lyric, Album, AudioFeatures, Word, Playlist


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
        except Error:
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
    spo_id, _, _ = get_all_spotify_info_name(name, artist_name, album_name)
    return spo_id


def get_all_spotify_info_name(name, artist_name, album_name=None):
    """
    Returns the Spotify info for a given song name, artist name and album name
    Used to match songs in database with Spotify information
    :param name: Name of song to search for (str)
    :param artist_name: Name of artist of song (str)
    :param album_name: Optional name of album of song (str)
    :return: {'name': Song name, 'id': Song ID}, ([{'name': Artist Name, 'id': Artist ID}]),
     {'name': Album Name, 'id': Album ID} from Spotify
    """
    q_string = "track:" + name + " artist:" + artist_name
    if album_name:
        q_string += " album:" + album_name
    try:
        results = sp.search(q=q_string, type='track', limit=1)
        results = results['tracks']['items'][0]
        return parse_spotify_track_object(results)
    except KeyError:
        # No Song was found
        return None, None, None


def get_all_spotify_info_id(spotify_id):
    """
    Returns the Spotify info for a given song id on Spotify
    :param spotify_id: spotify id of the song
    :return: {'name': Song name, 'id': Song ID}, ([{'name': Artist Name, 'id': Artist ID}]),
     {'name': Album Name, 'id': Album ID} from Spotify
    """
    try:
        result = sp.track(spotify_id)
        return parse_spotify_track_object(result)
    except SpotifyException:
        return None, None, None


def parse_spotify_track_object(track):
    """
    Extracts the Spotify information from a Spotify Track object
    :param track: Spotify Track Object from API 
    :return: {'name': Song name, 'id': Song ID}, ([{'name': Artist Name, 'id': Artist ID}]),
     {'name': Album Name, 'id': Album ID} from Spotify
    """
    artists = track['artists']
    artist_info = [{'name': a['name'], 'id': a['id']} for a in artists]
    album_info = {'name': track['album']['name'], 'id': track['album']['id']}
    song_info = {'name': track['name'], 'id': track['id']}
    return song_info, artist_info, album_info


def get_mxm_id(name, artist_name):
    """
    Returns the Musixmatch id for the song matching name and artist name
    :param name: Name of the song (str)
    :param artist_name: Name of the artist (str)
    :return: musixmatch id of the song
    """
    song_id, _, _, _ = get_all_mxm_info(name, artist_name)
    return song_id


def get_all_mxm_info(name, artist_name):
    """
    Returns all of the musixmatch ids for a given song
    Used to match songs in database with musixmatch
    :param name: Name of the song (str)
    :param artist_name: Name of the artist (str)
    :return: Song ID, (Artist Name, Artist ID), Album ID from musixmatch
    """
    query_string = 'matcher.track.get'
    keywords = {'q_artist': unidecode(artist_name),
                'q_track': unidecode(name), 'apikey': musixmatch_key}
    # response = requests.get(str(Request(query_string, keywords))).json()
    response = requests.get(str(Request(query_string, keywords))).json()
    if response['message']['header']['status_code'] == 404:
        return None, None, None, None
    response = response['message']['body']['track']
    artist_id = response['artist_id']
    art_name = response['artist_name']
    album_id = response['album_id']
    song_id = response['track_id']
    return song_id, art_name, artist_id, album_id


def build_song_from_name(name, artist_name):
    """
    Returns a Song that matches the song name and artist name provided
    Creates the object and fetches related data if the song is not in the database
    :param name: Name of the song (str)
    :param artist_name: Name of the artist (str)
    :return: Song object representing Song with provided name and artist, Whether new song was created (boolean)
    """
    spo_song_info, spo_artist_info, spo_album_info = get_all_spotify_info_name(name, artist_name)
    if Song.objects.filter(spotify_id=spo_song_info['id']).exists():
        # Song Already Exists
        return Song.objects.get(spotify_id=spo_song_info['id']), False
    mxm_song_id, mxm_artist_name, mxm_artist_id, mxm_album_id = get_all_mxm_info(name, artist_name)
    if Song.objects.filter(mxm_tid=mxm_song_id).exists():
        return Song.objects.get(mxm_tid=mxm_song_id), False
    return build_song(spo_song_info, spo_artist_info, spo_album_info,
                      mxm_song_id, mxm_artist_name, mxm_artist_id, mxm_album_id), True


def build_song_from_id(spotify_id):
    """
    Returns a Song that matches the spotify ID provided
    Creates the object and fetches related data is the song is not in the database
    :param spotify_id: Spotify ID (str)
    :return: Song object matching provided Spotify ID, Whether new song was created (boolean)
    """
    if Song.objects.filter(spotify_id=spotify_id).exists():
        return Song.objects.get(spotify_id=spotify_id), False
    spo_song_info, spo_artist_info, spo_album_info = get_all_spotify_info_id(spotify_id)
    mxm_song_id, mxm_artist_name, mxm_artist_id, mxm_album_id = get_all_mxm_info(spo_song_info['name'],
                                                                                 spo_artist_info[0]['name'])
    if Song.objects.filter(mxm_tid=mxm_song_id).exists():
        return Song.objects.get(mxm_tid=mxm_song_id), False
    return build_song(spo_song_info, spo_artist_info, spo_album_info, mxm_song_id, mxm_artist_name,
                      mxm_artist_id, mxm_album_id), True


def build_song(spo_song_info, spo_artist_info, spo_album_info,
               mxm_song_id, mxm_artist_name, mxm_artist_id, mxm_album_id):
    """
    Builds a Song object for the song matching the provided information and creates and dependencies that 
    don't exist. Adds or creates all of the artists and the album of the song from information from Spotify
    Also creates an AudioFeature for the song
    :param spo_song_info: Spotify Song information {'name': Song Name, 'id': Song Spotify ID}
    :param spo_artist_info: Spotify Artist information [{'name': Artist Name, 'id': Artist Spotify ID}]
    :param spo_album_info: Spotify Album information {'name': Album Name, 'id': Album Spotify ID}
    :param mxm_song_id: Musixmatch Song ID (str)
    :param mxm_artist_name: Musixmatch Artist Name (str)
    :param mxm_artist_id: Musixmatch Artist ID (str)
    :param mxm_album_id: Musixmatch Album ID(str)
    :return: Created Song Object
    """
    artists = []
    for sp_artist in spo_artist_info:
        if Artist.objects.filter(spotify_id=sp_artist['id']).exists():
            artists.append(Artist.objects.get(spotify_id=sp_artist['id']))
        elif mxm_artist_id and Artist.objects.filter(mxm_id=mxm_artist_id).exists():
            artists.append(Artist.objects.get(mxm_id=mxm_artist_id))
        else:
            artist = Artist.objects.create(name=sp_artist['name'])
            artist.spotify_id = sp_artist['id']
            if mxm_artist_name == sp_artist['name']:
                artist.mxm_id = mxm_artist_id
            artist.save()
            artists.append(artist)
    print("%d artists" % len(artists))
    if Album.objects.filter(spotify_id=spo_album_info['id']).exists():
        album = Album.objects.get(spotify_id=spo_album_info['id'])
    elif mxm_album_id and Album.objects.filter(mxm_id=mxm_album_id).exists():
        album = Album.objects.get(mxm_id=mxm_album_id)
    else:
        album = Album.objects.create(name=spo_album_info['name'], artist=artists[0])
        album.spotify_id = spo_album_info['id']
        album.mxm_id = mxm_album_id
        album.save()
    song = Song.objects.create(name=spo_song_info['name'], spotify_id=spo_song_info['id'],
                               mxm_tid=mxm_song_id, album=album)
    song.save()
    for artist in artists:
        song.artist.add(artist)
    get_audio_features([song])
    if mxm_song_id:
        lyricize(song)
    return song


def mxm_search_lyrics(name, artist_name):
    """
    Returns 30% of the lyrics of the song matching the information provided
    Lyrics are limited to 30% because of musixmatch policy
    :param name: Name of the song (str)
    :param artist_name: Name of the artist (str)
    :return: 30% of the lyrics of the song
    """
    mxm_id = get_mxm_id(name, artist_name)
    return mxm_get_lyrics(mxm_id)


def mxm_get_lyrics(mxm_id):
    """
    Returns 30% of the lyrics of the song matching the provided musixmatch id
    :param mxm_id: Musixmatch id (str)
    :return: 30% of the lyrics of the song
    """
    query_string = 'track.lyrics.get'
    keywords = {'track_id': mxm_id, 'apikey': musixmatch_key}
    # response = requests.get(str(Request(query_string, keywords))).json()
    response = requests.get(str(Request(query_string, keywords))).json()['message']
    if response['header']['status_code'] == 404:
        return ''
    lyrics = response['body']['lyrics']['lyrics_body']
    return lyrics[:lyrics.find('*')]


def get_audio_features(songs):
    """
    Creates audio features for all of the songs in the provided list. If the song doesn't have a spotify id, 
    one is fetched from the Spotify API. Takes a list of songs because AudioFeature API allows for multiple IDs
    to be passed at once
    :param songs: list of song objects to get audio features for [Song]
    :return: None
    """
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
    """
    Creates an AudioFeature object for the song with the provided audio feature information from Spotify
    :param song: Song in database (Song)
    :param features: audio features from the Spotify API (dict)
    :return: None
    """
    af = AudioFeatures.objects.create(
        song=song,
        acousticness=features['acousticness'] if features['acousticness'] else 9,
        danceability=features['danceability'] if features['danceability'] else 0,
        duration_ms=features['duration_ms'],
        energy=features['energy'] if features['energy'] else 0,
        instrumentalness=features['instrumentalness'] if features['instrumentalness'] else 0,
        key=features['key'],
        liveness=features['liveness'] if features['liveness'] else 0,
        loudness=features['loudness'],
        mode=features['mode'],
        speechiness=features['speechiness'] if features['speechiness'] else 0,
        tempo=features['tempo'],
        time_signature=features['time_signature'],
        valence=features['valence'] if features['valence'] else 0
    )
    af.save()


def lyricize(song):
    """
    Creates lyric objects in the database for the given song
    :param song: song to get lyrics for (Song)
    :return: None
    """
    lyrics = mxm_get_lyrics(song.mxm_tid)
    bow = bag_of_wordize(lyrics)
    create_lyrics(song, bow)


stemmer = nltk.stem.PorterStemmer()


def bag_of_wordize(lyrics):
    """
    Tokenizes and creates a bag of words with counts for a given string
    :param lyrics: lyrics of a song (str)
    :return: dictionary of {'word': word_count}
    """
    tokens = nltk.word_tokenize(lyrics)
    stems = [stemmer.stem(token) for token in tokens]
    bag_of_words = collections.Counter(stems)
    return bag_of_words


def create_lyrics(song, bag_of_words):
    """
    Creates lyrics objects in the database for the provided bag of words
    :param song: song object containing lyrics
    :param bag_of_words: bag of words with counts {'word': word_count}
    :return: None
    """
    for word, count in bag_of_words.iteritems():
        word_obj, _ = Word.objects.get_or_create(word=word)
        Lyric.objects.create(word=word_obj, song=song, count=count, is_test=0, mxm_id=song.mxm_tid).save()


def browse_playlists():
    """
    Browses all the Spotify Categories and creates playlists that haven't been created yet
    :return: None
    """
    # TODO
    pass


def fetch_category_playlists(spotify_catagory_id):
    """
    Fetches all playlists in the specified category and creates any playlists that don't already exist
    :param spotify_catagory_id: valid spotify category ID (str)
    :return: None
    """
    for p in sp.category_playlists(category_id=spotify_catagory_id,limit=50)['playlists']['items']:
        playlist, _ = Playlist.objects.get_or_create(
            name=p['name'],
            spotify_id=p['id']
        )

        print(p['name'], p['id'])
        print('*' * 20)
        request = sp.user_playlist_tracks(p['owner']['id'], playlist_id=p['id'])
        for s in request['items']:
            song, _ = build_song_from_id(s['track']['id'])
            playlist.songs.add(song)
            print(song.spotify_id)
        print()

