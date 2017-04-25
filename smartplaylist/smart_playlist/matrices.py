import cPickle as pickle
import logging
import time
from scipy import sparse
import numpy as np

from smart_playlist.models import Song

logger = logging.getLogger(__name__)

doc_freq_pickle = "/usr/local/src/app/pickles/doc_freq.pickle"
inv_index_pickle = '/usr/local/src/app/pickles/inv_index.pickle'
doc_norm_pickle = '/usr/local/src/app/pickles/doc_norms.pickle'
af_pickle = '/usr/local/src/app/pickles/audio_matrix.pickle'
playlist_pickle = '/usr/local/src/app/pickles/playlist_pickle.pickle'

good_features = ['danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence']

N_CLUST = 1000

song_count = -1
doc_freq = np.array([])
inv_index = {}
doc_norm = {}
af_clusters = None
playlist_concurrence = None
playlist_norm = None
initialized = False


def load_lyrics():
    global song_count, doc_freq, inv_index, doc_norm
    start = time.time()
    with open(doc_freq_pickle, 'rb') as f:
        doc_freq = pickle.load(f)
    temp = time.time()
    logger.info("Loaded Document Frequency in %s" % (temp - start))
    start = temp
    with open(inv_index_pickle, 'rb') as f:
        inv_index = pickle.load(f)
    temp = time.time()
    logger.info("Loaded Inverse Index in %s" % (temp - start))
    start = temp
    with open(doc_norm_pickle, 'rb') as f:
        doc_norm = pickle.load(f)
    logger.info("Loaded Document Norms in %s" % (temp - start))


def load_audio():
    global af_clusters
    start = time.time()
    with open(af_pickle, 'rb') as f:
        af_clusters = pickle.load(f)
    temp = time.time()
    logger.info("Loaded Audio Feature Clusters in %s" % (temp - start))


def load_playlist():
    global playlist_concurrence, playlist_norm
    start = time.time()
    with open(playlist_pickle, 'rb') as f:
        playlist_song = pickle.load(f)
    logger.info("Loaded Playlist Song Matrix in %s" % (time.time() - start))
    playlist_concurrence = playlist_song.T.dot(playlist_song)
    playlist_norm = sparse.linalg.norm(playlist_song, axis=0)
    temp = time.time()
    logger.info("Loaded Playlist Concurrence in %s" % (temp - start))


def load_matrices():
    global song_count, initialized
    logger.info("Loading Matrices")
    song_count = Song.objects.count()
    try:
        load_lyrics()
        load_audio()
        load_playlist()
        initialized = True
        logger.info("Loaded Matrices")
    except IOError as e:
        logger.info("Unable to load matrices")
        logger.exception(e)
