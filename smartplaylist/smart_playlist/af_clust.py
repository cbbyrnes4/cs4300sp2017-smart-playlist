import cPickle
import logging

from sklearn import cluster

N_CLUST = 300

logger = logging.getLogger(__name__)

af_pickle = '/usr/src/app/pickles/audio_matrix.pickle'

matrix = None
clusters = None


def load_clusters():
    global clusters, matrix
    try:
        with open(af_pickle, 'rb') as f:
            matrix = cPickle.load(f)
        clusters = cluster.KMeans(n_clusters=N_CLUST).fit(matrix)
    except IOError as e:
        logger.info("Unable to load clusters")
        logger.exception(e)


def get_cluster(song_id):
    return clusters.predict(matrix[song_id - 1])


def get_songs_in_cluster(cluster_id):
    return [ind + 1 for ind, clust in enumerate(clusters.labels_) if clust == cluster_id]


def get_matching_song_ids(song_id):
    return get_songs_in_cluster(get_cluster(song_id))
