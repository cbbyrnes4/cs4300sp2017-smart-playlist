import logging

from smart_playlist import matrices
from smart_playlist.models import AudioFeatures

logger = logging.getLogger(__name__)


def get_cluster(song_id):
    song_af = [val for key, val in AudioFeatures.objects.get(song_id=song_id)
               if key in matrices.good_features]
    return matrices.af_clusters.predict(song_af)


def get_songs_in_cluster(cluster_id):
    return {ind + 1 for ind, clust in enumerate(matrices.af_clusters.labels_) if clust == cluster_id}


def get_matching_song_ids(song_id):
    return get_songs_in_cluster(get_cluster(song_id))
