# Create your views here.
import logging

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render_to_response, render
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from unidecode import unidecode

import json
import spotipy
from spotipy import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials

from smart_playlist import search_methods, matrices, db_builder
from smart_playlist.models import Song, Artist

logger = logging.getLogger(__name__)

spotify_key = 'd305abf923f54ff0b2bee3ae17af289d'
spotify_secret = '55b73d4d03a44a309973c0693edbeaf9'

spo_cred_manager = SpotifyClientCredentials(spotify_key, spotify_secret)
sp = spotipy.Spotify(client_credentials_manager=spo_cred_manager)

keys = {0: 'C', 1: 'C#', 2: 'D', 3: 'D#', 4: 'E', 5: 'F', 6: 'F#', 7: 'G', 8: 'G#', 9: 'A', 10: 'A#', 11: 'B'}


def search(request):
    query_song = None
    songs = None
    query = None
    query_features = None
    if not matrices.initialized:
        matrices.load_matrices()
    if request.GET.get('song'):
        song = request.GET.get('song')
        artist = request.GET.get('artist')
        if request.GET.get('version') == '1':
            logger.info("Using V1")
            top_songs = search_methods.search_v1(song, artist)
        elif request.GET.get('version') == '2':
            logger.info("Using V2")
            top_songs = search_methods.search_v2(song, artist)
        else:
            logger.info("Using V3")
            alpha = float(request.GET.get('alpha')) / 100
            beta = float(request.GET.get('beta')) / 100
            gamma = float(request.GET.get('gamma')) / 100
            top_songs = search_methods.search_v3(song, artist, alpha, beta, gamma)

        output = top_songs[1:21]
        query_song = db_builder.build_song_from_name(song, artist)[0]
        songs = []

        for i, lyric, cluster, playlist, total in output:
            spotify_song = sp.track(str(Song.objects.values_list('spotify_id').get(id=i)[0]))

            song_json = {'song': unidecode(Song.objects.get(id=i).__str__()), 
                'lyric': lyric, 
                'cluster': cluster, 
                'playlist': playlist, 
                'total': total,
                'features': search_methods.get_similar_features(i, query_song.id),
                'preview': spotify_song['preview_url'],
                'artwork': spotify_song['album']['images'][0]['url']} 

            songs.append(song_json)

        query = (song, artist)
        query_features = search_methods.get_features(query_song.id)
        spotify_query = sp.track(str(query_song.spotify_id))
        query_song = {'name': query_song.__str__(),
                      'preview': spotify_query['preview_url'],
                      'artwork': spotify_query['album']['images'][0]['url'] }

    return render(request, "smart_playlist/base.html", context=
    { 'songs': songs, 'query': query, 'query_song': query_song , 'query_features': query_features })


def find_song(request):
    song_name = str(request.GET.get('term')).strip('\'')
    songs = Song.objects.filter(name__icontains=song_name)[:10]
    results = []

    for song in songs:
        song_json = {}
        song_json['value'] = unidecode(song.name)
        artists = []

        for artist in song.artist.all():
            artists.append(artist.name)
        song_json['label'] =  unidecode(song.name + " by " + ", ".join(artists))

        song_json['id'] = unidecode(artists[0])
        results.append(song_json)

    return JsonResponse(results, safe=False)


def find_artist(request):
    artist_name = str(request.GET.get('term')).strip('\'')
    artists = Artist.objects.filter(name__icontains=artist_name)[:10]
    results = []

    for artist in artists:
        artist_json = {}
        artist_json['value'] = unidecode(artist.name)

        results.append(artist_json)

    return JsonResponse(results, safe=False)



