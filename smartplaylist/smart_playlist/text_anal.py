import cPickle as pickle
import logging

import numpy as np

from smart_playlist.models import Lyric, Song

song_count = -1
doc_freq = np.array([])
song_word = np.array([])
good_words = None
word_to_index = {}
pmi = np.array([[]])
initialized = False
logger = logging.getLogger(__name__)

doc_freq_pickle = "/usr/src/app/pickles/doc_freq.pickle"
song_word_pickle = '/usr/src/app/pickles/song_word.pickle'
good_words_pickle = '/usr/src/app/pickles/good_words.pickle'
word_to_index_pickle = '/usr/src/app/pickles/word_to_index.pickle'
pmi_pickle = '/usr/src/app/pickles/pmi.pickle'


def get_lyrically_overlapping_songs(song):
    """
    Returns all of the song ids of songs that share a lyric with the provided song
    :param song: song to match with (Song)
    :return: set of song ids
    """
    song_words = Lyric.objects.filter(song=song, word__in=good_words).values('word').distinct()
    lyrics = Lyric.objects.filter(word__in=song_words)
    songs_set = lyrics.exclude(song=song).values('song_id').distinct()
    return songs_set


def get_cosine_top_songs(song):
    overlap = get_lyrically_overlapping_songs(song)
    cos_sims = calc_cosine_sims(song, overlap)
    top_indices = np.argsort(cos_sims)[::-1]
    return [(overlap[i]['song_id'], cos_sims[i]) for i in top_indices]


def get_pmi_top_songs(song):
    top_indices = np.argsort(pmi[song.id - 1])[::-1]
    return [(i + 1, pmi[song.id - 1][i]) for i in top_indices if pmi[song.id - 1][i] > 0]


def calc_cosine_sims(song, overlapping_songs):
    song_tf = np.zeros(good_words.count())
    for lyric in song.lyric_set.filter(word__in=good_words):
        try:
            df = doc_freq[word_to_index[lyric.word.word]]
        except IndexError:
            df = 1
        song_tf[word_to_index[lyric.word.word]] = float(lyric.count) * np.log(song_count / df)
    cos_sims = np.zeros(len(overlapping_songs))
    for ind, olap in enumerate(overlapping_songs):
        cos_sims[ind] = cosine_sim(song_tf, olap)
    return cos_sims


def cosine_sim(q, d):
    song_vec = tfidf_vec(d['song_id'])
    return np.dot(q, song_vec) / (np.linalg.norm(q) * np.linalg.norm(song_vec))


def tfidf_vec(song_id):
    return song_word[song_id - 1] * np.log(song_count / doc_freq)


def load_matrices():
    global song_count, doc_freq, song_word, good_words, word_to_index, pmi, initialized
    logger.info("Loading Matrices")
    song_count = Song.objects.count()
    try:
        with open(good_words_pickle, 'rb') as f:
            good_words = pickle.load(f)
        with open(word_to_index_pickle, 'rb') as f:
            word_to_index = pickle.load(f)
        with open(doc_freq_pickle, 'rb') as f:
            doc_freq = pickle.load(f)
        with open(song_word_pickle, 'rb') as f:
            song_word = pickle.load(f)
        tfidf_mat = song_word * np.log(song_count / doc_freq)
        pmi = np.dot(tfidf_mat, tfidf_mat.T)
        norm = np.linalg.norm(song_word, axis=1)
        pmi /= norm
        pmi = (pmi.T / norm).T
        initialized = True
        logger.info("Loaded Matrices")
    except IOError as e:
        logger.info("Unable to load matrices")
        logger.exception(e)


def refresh_matrices(song):
    # TODO: Make more efficient
    pass
