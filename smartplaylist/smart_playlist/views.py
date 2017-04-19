# Create your views here.
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render_to_response
from unidecode import unidecode

from smart_playlist import db_builder, text_anal
from smart_playlist.models import Song


def search(request):
    output = ''
    songs = None
    query = None
    if not text_anal.initialized:
        text_anal.load_matrices()
    if request.GET.get('song'):
        song = request.GET.get('song')
        artist = request.GET.get('artist')
        song, created = db_builder.build_song_from_name(song, artist)
        if created:
            text_anal.refresh_matrices(song)
            top_songs = text_anal.get_cosine_top_songs(song)
        else:
            top_songs = text_anal.get_pmi_top_songs(song)
        paginator = Paginator(top_songs, 10)
        page = request.GET.get('page')
        try:
            output = paginator.page(page)
        except PageNotAnInteger:
            output = paginator.page(1)
        except EmptyPage:
            output = paginator.page(paginator.num_pages)
        # TODO Figure out how to display utf-8 chars
        songs = [unidecode(Song.objects.get(id=i).__str__()) for i, score in output]
        query = "%s: %s" % (song, artist)

    return render_to_response('smart_playlist/base.html',
                              {'songs': songs,
                               'output': output,
                               'query': query,
                               'magic_url': request.get_full_path(),
                               })
