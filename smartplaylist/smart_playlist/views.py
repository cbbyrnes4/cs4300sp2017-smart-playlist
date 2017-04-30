# Create your views here.
import logging

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render_to_response, render
from django.http import HttpResponse, JsonResponse
from unidecode import unidecode

import json
import spotipy
from spotipy import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials

from smart_playlist import search_methods, matrices
from smart_playlist.models import Song, Artist

logger = logging.getLogger(__name__)

spotify_key = 'd305abf923f54ff0b2bee3ae17af289d'
spotify_secret = '55b73d4d03a44a309973c0693edbeaf9'

spo_cred_manager = SpotifyClientCredentials(spotify_key, spotify_secret)
sp = spotipy.Spotify(client_credentials_manager=spo_cred_manager)


# def search(request):
#     output = ''
#     songs = None
#     query = None
#     if not matrices.initialized:
#         matrices.load_matrices()
#     if request.GET.get('song'):
#         song = request.GET.get('song')
#         artist = request.GET.get('artist')
#         if request.GET.get('version') == '1':
#             logger.info("Using V1")
#             top_songs = search_methods.search_v1(song, artist)
#         elif request.GET.get('version') == '2':
#             logger.info("Using V2")
#             top_songs = search_methods.search_v2(song, artist)
#         else:
#             logger.info("Using V3")
#             top_songs = search_methods.search_v3(song, artist)
#         paginator = Paginator(top_songs, 10)
#         page = request.GET.get('page')
#         try:
#             output = paginator.page(page)
#         except PageNotAnInteger:
#             output = paginator.page(1)
#         except EmptyPage:
#             output = paginator.page(paginator.num_pages)
#         # TODO Figure out how to display utf-8 chars
#         songs = [(unidecode(Song.objects.get(id=i).__str__()), lyric, cluster, playlist, total) for i, lyric, cluster, playlist, total in output]
#         query = unidecode(Song.objects.get(id=top_songs[0][0]).__str__())
    
#     return render_to_response('smart_playlist/base.html',
#                               {'songs': songs,
#                                'output': output,
#                                'query': query,
#                                'magic_url': request.get_full_path(),
#                                })

def search(request):
    output = ''
    songs = None
    query = None
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
            top_songs = search_methods.search_v3(song, artist)
        output = top_songs[1:21]
        songs = [{'song': unidecode(Song.objects.get(id=i).__str__()), 
                 'lyric': lyric, 
                 'cluster': cluster, 
                 'playlist': playlist, 
                 'total': total, 
                 'preview': sp.track(str(Song.objects.values_list('spotify_id').get(id=i)[0]))['preview_url']} 
                 for i, lyric, cluster, playlist, total in output]
        query = unidecode(Song.objects.get(id=top_songs[0][0]).__str__())    
    return render(request, "smart_playlist/base.html", context={ 'songs': songs, 'query': query })

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



