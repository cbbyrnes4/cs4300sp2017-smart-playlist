# Create your views here.
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render_to_response

from smart_playlist import db_builder, text_anal


def search(request):
    output = ''
    if request.GET.get('song'):
        song = request.GET.get('song')
        artist = request.GET.get('artist')
        song = db_builder.build_song_from_name(song, artist)
        top_songs = text_anal.get_top_songs(song)
        top_songs = [song for song, score in top_songs]
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
