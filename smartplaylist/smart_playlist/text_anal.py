import logging
from collections import defaultdict

import numpy as np

import matrices

logger = logging.getLogger(__name__)


def get_cosine_top_songs(song):
    cos_sims = calc_cosine_sims(song)
    return {song: score for song, score in cos_sims.iteritems() if score > 0}


def calc_cosine_sims(song):
    song_scores = defaultdict(float)
    q_norm = 0
    for lyric in song.lyric_set.all():
        for doc, count in matrices.inv_index[lyric.word_id]:
            song_scores[doc] += tfidf(lyric.word_id, lyric.count) * tfidf(lyric.word_id, count)
        q_norm += (tfidf(lyric.word_id, lyric.count)) ** 2
    q_norm = np.sqrt(q_norm)
    for doc in song_scores.keys():
        song_scores[doc] /= matrices.doc_norm[doc]
        song_scores[doc] /= q_norm
    return song_scores


def tfidf(word_id, count):
    return count * np.log(matrices.song_count / (matrices.doc_freq[word_id] + 1))




def refresh_matrices(song):
    # TODO: Make more efficient
    pass
