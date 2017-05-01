import logging
from operator import itemgetter

from django.db.models import Max
from django.http import Http404

from smart_playlist import db_builder, text_anal, af_clust, playlist, matrices
from smart_playlist.models import Song, Lyric, AudioFeatures, Word

logger = logging.getLogger(__name__)


def search_v1(song, artist):
    song, created = db_builder.build_song_from_name(song, artist)
    if created:
        logger.info("Created song %s" % song)
        text_anal.refresh_matrices(song)
    songs = [(song, score) for song, score in
             text_anal.get_cosine_top_songs(song).iteritems()]
    songs.sort(key=itemgetter(1), reverse=True)
    return [(song, score, 0, 0, score) for song, score in songs]


ALPHA_1 = 1
BETA_1 = 1
GAMMA_1 = 1


def search_v2(song, artist):
    num_ids = Song.objects.all().aggregate(Max('id'))['id__max']
    song, created = db_builder.build_song_from_name(song, artist)
    if created or song.id >= matrices.playlist_concurrence.shape[0]:
        playlist_rank = {}
    else:
        playlist_rank = playlist.playlist_pmi(song.id)
    lyric_rank = text_anal.get_cosine_top_songs(song)
    cluster_songs = af_clust.get_matching_song_ids(song.id)
    scores = [(i,
               (ALPHA_1 * lyric_rank[i] if i in lyric_rank else 0) +
               (BETA_1 * 1 if i in cluster_songs else 0) +
               (GAMMA_1 * playlist_rank[i] if i in playlist_rank else 0)) for
              i in range(num_ids)]
    scores.sort(key=itemgetter(1), reverse=True)
    return [(i,
             (ALPHA_1 * lyric_rank[i] if i in lyric_rank else 0),
             (BETA_1 * 1 if i in cluster_songs else 0),
             (GAMMA_1 * playlist_rank[i] if i in playlist_rank else 0),
             score)
            for i, score in scores]


def search_v3(song, artist, alpha=ALPHA_1, beta=BETA_1, gamma=GAMMA_1):
    num_ids = Song.objects.all().aggregate(Max('id'))['id__max']
    song, created = db_builder.build_song_from_name(song, artist)

    if song == None:
        raise Http404("Song does not exist on Spotify")

    if created or song.id >= matrices.playlist_concurrence.shape[0]:
        playlist_rank = {}
    else:
        playlist_rank = playlist.playlist_pmi(song.id)
    lyric_rank = text_anal.get_cosine_top_songs(song)
    cluster_songs, struct_songs = af_clust.get_both_sets(song.id)
    scores = [(i,
               (alpha * lyric_rank[i] if i in lyric_rank else 0) +
               (float(beta)/2 * 1 if i in cluster_songs else 0) +
               (float(beta)/2 if i in struct_songs else 0) +
               (gamma * playlist_rank[i] if i in playlist_rank else 0)) for
              i in range(num_ids)]
    scores.sort(key=itemgetter(1), reverse=True)
    return [(i,
             (alpha * lyric_rank[i] if i in lyric_rank else 0),
             (float(beta) / 2 * 1 if i in cluster_songs else 0) +
             (float(beta) / 2 if i in struct_songs else 0),
             (gamma * playlist_rank[i] if i in playlist_rank else 0),
             score)
            for i, score in scores]


def get_features(song):
    top_lyrics = Lyric.objects.filter(song_id=song).order_by('count').reverse().values('word__word', 'count')
    audio_features = [(key, val) for key, val in AudioFeatures.objects.get(song_id=song) if key in matrices.good_features]
    struct_features = [(key, val) for key, val in AudioFeatures.objects.get(song_id=song) if key in matrices.structure_features]
    return {'lyrics': top_lyrics, 'af': audio_features,
            'sf': struct_features }


def get_similar_features(song, q_id):
    af = [(key, val, val2, val - val2) for (key, val), (key1, val2) in
          zip(AudioFeatures.objects.get(song_id=song), AudioFeatures.objects.get(song_id=q_id)) if
          key in matrices.good_features]
    af.sort(key=lambda x: x[3]**2)
    audio_features = [(key, sv, qv) for key, sv, qv, _ in af][:3]
    sf = [(key, val, val2, val - val2) for (key, val), (key1, val2) in
          zip(AudioFeatures.objects.get(song_id=song), AudioFeatures.objects.get(song_id=q_id)) if
          key in matrices.structure_features]
    af.sort(key=lambda x: x[3]**2)
    struct_features = [(key, sv, qv) for key, sv, qv, _ in sf][:3]
    try:
        pc = matrices.playlist_concurrence[song-1, q_id-1]
    except IndexError:
        pc = 0

    query_lyrics = Lyric.objects.filter(song_id=q_id)
    song_lyrics = Lyric.objects.filter(song_id=song)
    good_words = Word.objects.filter(id__in=query_lyrics.values('word_id')).filter(id__in=song_lyrics.values('word_id')).values('id')
    good_query_lyrics = query_lyrics.filter(word_id__in=good_words)
    good_song_lyrics = song_lyrics.filter(word_id__in=good_words)

    overlaps = [(ql.word_id, ql.count, sl.count) for ql, sl in
                zip(good_query_lyrics.order_by('word_id'), good_song_lyrics.order_by('word_id'))]

    tf_scores = [(wid, text_anal.tfidf(wid, qc)*text_anal.tfidf(wid, sc), qc, sc) for wid, qc, sc in overlaps]
    tf_scores.sort(key=itemgetter(1), reverse=True)
    top_lyrics = [(Word.objects.get(id=wid).word, text_anal.tfidf(wid, qc), text_anal.tfidf(wid, sc))
                  for wid, _, qc, sc in tf_scores[:10]]
    return {'af': audio_features, 'sf': struct_features, 'pc': pc, 'lyrics': top_lyrics}
