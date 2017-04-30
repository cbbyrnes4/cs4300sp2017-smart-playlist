import logging

from smart_playlist import matrices
from smart_playlist.db_builder import get_audio_features
from smart_playlist.models import AudioFeatures

logger = logging.getLogger(__name__)


def get_audio_cluster(song_id):
    song_af = [val for key, val in AudioFeatures.objects.get(song_id=song_id)
               if key in matrices.good_features]
    return matrices.af_clusters.predict(song_af)


def get_struct_cluster(song_id):
    song_af = [val for key, val in AudioFeatures.objects.get(song_id=song_id)
               if key in matrices.structure_features]
    return matrices.struct_clusters.predict(song_af)


def get_songs_in_cluster(af_id):
    return {ind + 1 for ind, af in
            enumerate(matrices.af_clusters.labels_)
            if af == af_id}


def get_songs_in_struct(struct_id):
    return {ind + 1 for ind, struct in
            enumerate(matrices.struct_clusters.labels_)
            if struct == struct_id}


def get_matching_song_ids(song_id):
    return get_songs_in_cluster(get_audio_cluster(song_id))


def get_both_sets(song_id):
    return get_songs_in_cluster(get_audio_cluster(song_id)), get_songs_in_struct(get_struct_cluster(song_id))
