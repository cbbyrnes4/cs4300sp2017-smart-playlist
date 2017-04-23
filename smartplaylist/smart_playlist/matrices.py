import cPickle as pickle
import logging
import time

import numpy as np
from sklearn import cluster

from smart_playlist.models import Song

logger = logging.getLogger(__name__)

doc_freq_pickle = "/usr/src/app/pickles/doc_freq.pickle"
song_word_pickle = '/usr/src/app/pickles/song_word.pickle'
good_words_pickle = '/usr/src/app/pickles/good_words.pickle'
word_to_index_pickle = '/usr/src/app/pickles/word_to_index.pickle'
pmi_pickle = '/usr/src/app/pickles/pmi.pickle'
af_pickle = '/usr/src/app/pickles/audio_matrix.pickle'
playlist_pickle = '/usr/src/app/pickles/audio_matrix.pickle'

N_CLUST = 1000

song_count = -1
doc_freq = np.array([])
song_word = np.array([])
good_words = None
word_to_index = {}
pmi = np.array([[]])
af_matrix = None
af_clusters = None
playlist_concurrence = None
initialized = False


def load_matrices():
    global song_count, doc_freq, song_word, good_words, word_to_index, pmi, af_clusters, af_matrix, \
        playlist_concurrence, initialized
    logger.info("Loading Matrices")
    start = time.time()
    song_count = Song.objects.count()
    try:
        with open(good_words_pickle, 'rb') as f:
            good_words = pickle.load(f)
        temp = time.time()
        logger.info("Loaded Good Words in %s" % (temp - start))
        start = temp
        with open(word_to_index_pickle, 'rb') as f:
            word_to_index = pickle.load(f)
        temp = time.time()
        logger.info("Loaded Word Index in %s" % (temp - start))
        start = temp
        with open(doc_freq_pickle, 'rb') as f:
            doc_freq = pickle.load(f)
        temp = time.time()
        logger.info("Loaded Document Frequency in %s" % (temp - start))
        start = temp
        with open(song_word_pickle, 'rb') as f:
            song_word = pickle.load(f)
        temp = time.time()
        logger.info("Loaded Song Word in %s" % (temp - start))
        start = temp
        tfidf_mat = song_word * np.log(song_count / doc_freq)
        pmi = np.dot(tfidf_mat, tfidf_mat.T)
        norm = np.linalg.norm(song_word, axis=1)
        pmi /= norm
        pmi = (pmi.T / norm).T
        temp = time.time()
        logger.info("Created PMI in %s" % (temp - start))
        start = temp
        with open(af_pickle, 'rb') as f:
            af_matrix = pickle.load(f)
        af_clusters = cluster.KMeans(n_clusters=N_CLUST).fit(af_matrix)
        temp = time.time()
        logger.info("Loaded Audio Feature Clusters in %s" % (temp - start))
        start = temp
        with open(playlist_pickle, 'rb') as f:
            playlist_song = pickle.load(f)
        playlist_concurrence = np.dot(playlist_song, playlist_song.T)
        norm = np.linalg.norm(playlist_song, axis=1)
        playlist_concurrence /= norm
        playlist_concurrence = (playlist_concurrence.T / norm).T
        temp = time.time()
        logger.info("Loaded Playlist Concurrence in %s" % (temp - start))
        start = temp
        initialized = True
        logger.info("Loaded Matrices")
    except IOError as e:
        logger.info("Unable to load matrices")
        logger.exception(e)
