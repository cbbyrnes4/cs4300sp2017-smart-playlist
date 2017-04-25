import cPickle as pickle
import logging
import os
import sys
import time
from collections import defaultdict

import django
import numpy as np
from django.db.models import Max
from scipy import sparse
from sklearn import cluster

django.setup()

from smart_playlist import matrices
from smart_playlist.models import Song, Word, Lyric, AudioFeatures, Playlist

logger = logging.getLogger(__name__)


def log_time(message, start):
    logger.info(message)
    end = time.time()
    logger.info("Elapsed time: %s" % (end - start))
    return end


def prune_data():
    start = time.time()
    Word.objects.filter(lyric__count=1).delete()
    log_time("Pruned Data", start)


def build_lyrics():
    start = time.time()
    num_ids = Song.objects.all().aggregate(Max('id'))['id__max']
    song_count = Song.objects.count()
    logger.info("Songs: %s" % song_count)
    start = log_time("Total Number of Words %s" % Word.objects.count(), start)
    inv_index = defaultdict(list)
    df = defaultdict(int)
    doc_lyrics = defaultdict(list)
    for lyric in Lyric.objects.all():
        inv_index[lyric.word_id].append((lyric.song_id, lyric.count))
        df[lyric.word_id] += 1
        doc_lyrics[lyric.song_id].append((lyric.word_id, lyric.count))
    start = log_time("Inverse Index and Document Frequency Created", start)
    doc_norms = defaultdict(float)
    for doc, postings in doc_lyrics.iteritems():
        for wid, count in postings:
            doc_norms[doc] += (count * np.log(song_count / df[wid])) ** 2
        doc_norms[doc] = np.math.sqrt(doc_norms[doc])

    if os.path.exists(matrices.doc_freq_pickle):
        os.remove(matrices.doc_freq_pickle)
    with open(matrices.doc_freq_pickle, 'wb') as f:
        pickle.dump(df, f)

    if os.path.exists(matrices.inv_index_pickle):
        os.remove(matrices.inv_index_pickle)
    with open(matrices.inv_index_pickle, 'wb') as f:
        pickle.dump(inv_index, f)

    if os.path.exists(matrices.doc_norm_pickle):
        os.remove(matrices.doc_norm_pickle)
    with open(matrices.doc_norm_pickle, 'wb') as f:
        pickle.dump(doc_norms, f)

    log_time("Wrote Lyrics Pickles", start)
    return num_ids


def build_audio(num_ids):
    start = time.time()
    audio_matrix = np.zeros((num_ids, 7))
    audio_features = AudioFeatures.objects.all()
    for af in audio_features:
        audio_matrix[af.song_id - 1] = [val for key, val in af if key in matrices.good_features]
    start = log_time("Audio Features Matrix Created", start)

    af_clusters = cluster.KMeans(n_clusters=matrices.N_CLUST).fit(audio_matrix)
    start = log_time("Audio Clusters Created", start)
    if os.path.exists(matrices.af_pickle):
        os.remove(matrices.af_pickle)
    with open(matrices.af_pickle, 'wb') as f:
        pickle.dump(af_clusters, f)
    log_time("Wrote AudioFeature Pickles", start)


def build_playlist(num_ids):
    start = time.time()
    playlist_song = np.zeros((Playlist.objects.all().aggregate(Max('id'))['id__max'], num_ids))
    for playlist in Playlist.objects.all():
        for song in playlist.songs.all():
            playlist_song[playlist.id - 1, song.id - 1] = 1
    start = log_time("Playlist Song Matrix Created", start)
    if os.path.exists(matrices.playlist_pickle):
        os.remove(matrices.playlist_pickle)
    with open(matrices.playlist_pickle, 'wb') as f:
        pickle.dump(sparse.csr_matrix(playlist_song), f)
    log_time("Wrote Playlist Pickles", start)


def build_matrices():
    # TODO: Make more efficient
    logger.info("Building Matrices")
    start = time.time()
    # prune_data()
    num_ids = build_lyrics()

    build_audio(num_ids)
    build_playlist(num_ids)
    log_time("Built Matrices", start)

if __name__ == "__main__":
    build_matrices()
    sys.exit(0)
