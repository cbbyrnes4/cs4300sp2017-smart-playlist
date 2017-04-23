# Create your views here.
import logging

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render_to_response
from unidecode import unidecode

from smart_playlist import search_methods, matrices
from smart_playlist.models import Song

logger = logging.getLogger(__name__)


def search(request, version):
    output = ''
    songs = None
    query = None
    if not matrices.initialized:
        matrices.load_matrices()
    if request.GET.get('song'):
        song = request.GET.get('song')
        artist = request.GET.get('artist')
        if version == '1':
            logger.info("Using V1")
            top_songs = search_methods.search_v1(song, artist)
        elif version == '2':
            logger.info("Using V2")
            top_songs = search_methods.search_v2(song, artist)
        else:
            logger.info("Using V3")
            top_songs = search_methods.search_v3(song, artist)
        paginator = Paginator(top_songs, 10)
        page = request.GET.get('page')
        try:
            output = paginator.page(page)
        except PageNotAnInteger:
            output = paginator.page(1)
        except EmptyPage:
            output = paginator.page(paginator.num_pages)
        # TODO Figure out how to display utf-8 chars
        songs = [(unidecode(Song.objects.get(id=i).__str__()), score) for i, score in output]
        query = unidecode(songs[0][0])

    return render_to_response('smart_playlist/base.html',
                              {'songs': songs,
                               'output': output,
                               'query': query,
                               'magic_url': request.get_full_path(),
                               })
