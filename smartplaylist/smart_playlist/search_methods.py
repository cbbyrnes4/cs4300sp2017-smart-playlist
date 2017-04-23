from operator import itemgetter

from django.db.models import Max

from smart_playlist import db_builder, text_anal, af_clust, playlist
from smart_playlist.models import Song


def search_v1(song, artist):
    song, created = db_builder.build_song_from_name(song, artist)
    if created:
        text_anal.refresh_matrices(song)
        return text_anal.get_cosine_top_songs(song)
    else:
        return text_anal.get_pmi_top_songs(song)


ALPHA_1 = 1
BETA_1 = 1
GAMMA_1 = 1


def search_v2(song, artist):
    num_ids = Song.objects.all().aggregate(Max('id'))['id__max']
    song, created = db_builder.build_song_from_name(song, artist)
    if created:
        lyric_rank = text_anal.get_cosine_top_songs(song)
        playlist_rank = {}
    else:
        lyric_rank = text_anal.get_pmi_top_songs(song)
        playlist_rank = playlist.playlist_pmi(song.id)
    cluster_songs = af_clust.get_matching_song_ids(song.id)
    scores = [(i,
               (ALPHA_1 * lyric_rank[i] if i in lyric_rank else 0) +
               (BETA_1 * 1 if i in cluster_songs else 0) +
               (GAMMA_1 * playlist_rank[i] if i in playlist_rank else 0)) for
              i in range(num_ids)]
    scores.sort(key=itemgetter(1), reverse=True)
    return scores

def search_v3(song, artist):
    pass
