import logging

from smart_playlist import matrices

logger = logging.getLogger(__name__)


def get_cluster(song_id):
    return matrices.af_clusters.predict(matrices.af_matrix[song_id - 1])


def get_songs_in_cluster(cluster_id):
    return {ind + 1 for ind, clust in enumerate(matrices.af_clusters.labels_) if clust == cluster_id}


def get_matching_song_ids(song_id):
    return get_songs_in_cluster(get_cluster(song_id))
