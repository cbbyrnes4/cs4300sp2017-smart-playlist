# Create your views here.
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render_to_response

from smart_playlist import db_builder, text_anal


def search(request):
    output = ''
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

    return render_to_response('smart_playlist/base.html',
                              {'output': output,
                               'magic_url': request.get_full_path(),
                               })
