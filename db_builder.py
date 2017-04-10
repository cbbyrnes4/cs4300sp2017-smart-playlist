import django
import requests
import spotipy
from django.core.exceptions import ObjectDoesNotExist
from musixmatch.api import Error, Request
from musixmatch.track import Track

django.setup()

# musixmatch_key = os.environ.get('MUSIXMATCH_KEY')
# spotify_id = os.environ.get('SPOTIFY_ID')
# spotify_secret = os.environ.get('SPOTIFY_SECRET')

musixmatch_key = 'f8192e15050fe5f070871e35d35251a2'

unauth_spotify = spotipy.Spotify()

from smart_playlist.models import Song, Artist, Lyric, Album


def search_mxm_for_info(mxm_id):
    """
    Searches the MusixMatch Database and creates a song object if one doesn't
    already exist for the mxm_id
    """
    song_match = Song.objects.filter(mxm_tid=mxm_id)
    if song_match.count() == 0:
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
    q_string = "track:" + name + " artist:" + artist_name
    if album_name:
        q_string += " album:" + album_name
    try:
        results = unauth_spotify.search(q=q_string, type='track', limit=1)
        results = results['tracks']['items'][0]
        print(results['name'])
        return results['id']
    except KeyError:
        # No Song was found
        return None


def get_mxm_id(name, artist_name):
    query_string = 'matcher.track.get'
    keywords = {'q_artist': artist_name, 'q_track': name, 'apikey': musixmatch_key}
    response = requests.get(str(Request(query_string, keywords))).json()
    return response['message']['body']['track']['track_id']


def mxm_search_lyrics(name, artist_name):
    mxm_id = get_mxm_id(name, artist_name)
    return mxm_get_lyrics(mxm_id)


def mxm_get_lyrics(mxm_id):
    query_string = 'track.lyrics.get'
    keywords = {'track_id': mxm_id, 'apikey': musixmatch_key}
    response = requests.get(str(Request(query_string, keywords))).json()
    lyrics = response['message']['body']['lyrics']['lyrics_body']
    return lyrics[:lyrics.find('*')]
