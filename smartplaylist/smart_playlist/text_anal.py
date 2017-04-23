import logging

import numpy as np

import matrices
from smart_playlist.models import Lyric

logger = logging.getLogger(__name__)


def get_lyrically_overlapping_songs(song):
    """
    Returns all of the song ids of songs that share a lyric with the provided song
    :param song: song to match with (Song)
    :return: set of song ids
    """
    song_words = Lyric.objects.filter(song=song, word__in=matrices.good_words).values('word').distinct()
    lyrics = Lyric.objects.filter(word__in=song_words)
    songs_set = lyrics.exclude(song=song).values('song_id').distinct()
    return songs_set


def get_cosine_top_songs(song):
    overlap = get_lyrically_overlapping_songs(song)
    cos_sims = calc_cosine_sims(song, overlap)
    top_indices = np.argsort(cos_sims)[::-1]
    return {overlap[i]['song_id']: cos_sims[i] for i in top_indices}


def get_pmi_top_songs(song):
    top_indices = np.argsort(matrices.pmi[song.id - 1])[::-1]
    return {i + 1: matrices.pmi[song.id - 1][i] for i in top_indices if matrices.pmi[song.id - 1][i] > 0}


def calc_cosine_sims(song, overlapping_songs):
    song_tf = np.zeros(matrices.good_words.count())
    for lyric in song.lyric_set.filter(word__in=matrices.good_words):
        try:
            df = matrices.doc_freq[matrices.word_to_index[lyric.word.word]]
        except IndexError:
            df = 1
        song_tf[matrices.word_to_index[lyric.word.word]] = float(lyric.count) * np.log(matrices.song_count / df)
    cos_sims = np.zeros(len(overlapping_songs))
    for ind, olap in enumerate(overlapping_songs):
        cos_sims[ind] = cosine_sim(song_tf, olap)
    return cos_sims


def cosine_sim(q, d):
    song_vec = tfidf_vec(d['song_id'])
    return np.dot(q, song_vec) / (np.linalg.norm(q) * np.linalg.norm(song_vec))


def tfidf_vec(song_id):
    return matrices.song_word[song_id - 1] * np.log(matrices.song_count / matrices.doc_freq)


def refresh_matrices(song):
    # TODO: Make more efficient
    pass
