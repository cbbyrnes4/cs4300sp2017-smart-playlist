import cPickle as pickle
import logging
import os
import sys
import time

import django
import numpy as np
from django.db.models import Max

django.setup()

from smart_playlist import matrices
from smart_playlist.models import Song, Word, Lyric, AudioFeatures, Playlist

logger = logging.getLogger(__name__)


def write_pickles():
    global doc_freq, song_word, good_words, word_to_index, audio_matrix, playlist_song
    if os.path.exists(matrices.doc_freq_pickle):
        os.remove(matrices.doc_freq_pickle)
    with open(matrices.doc_freq_pickle, 'wb') as f:
        pickle.dump(doc_freq, f)
    if os.path.exists(matrices.song_word_pickle):
        os.remove(matrices.song_word_pickle)
    with open(matrices.song_word_pickle, 'wb') as f:
        pickle.dump(song_word, f)
    if os.path.exists(matrices.word_to_index_pickle):
        os.remove(matrices.good_words_pickle)
    with open(matrices.good_words_pickle, 'wb') as f:
        pickle.dump(good_words, f)
    if os.path.exists(matrices.word_to_index_pickle):
        os.remove(matrices.word_to_index_pickle)
    with open(matrices.word_to_index_pickle, 'wb') as f:
        pickle.dump(word_to_index, f)
    if os.path.exists(matrices.af_pickle):
        os.remove(matrices.af_pickle)
    with open(matrices.af_pickle, 'wb') as f:
        pickle.dump(audio_matrix, f)
    if os.path.exists(matrices.playlist_pickle):
        os.remove(matrices.playlist_pickle)
    with open(matrices.playlist_pickle, 'wb') as f:
        pickle.dump(playlist_song, f)


def build_matrices():
    # TODO: Make more efficient
    global doc_freq, song_word, good_words, word_to_index, audio_matrix, playlist_song
    start = time.time()
    num_ids = Song.objects.all().aggregate(Max('id'))['id__max']
    song_count = Song.objects.count()
    logger.info("Songs: %s" % song_count)
    logger.info("Total Number of Words %s" % Word.objects.count())
    logger.info("Elapsed Time: %s" % (time.time() - start))
    max_thresh = song_count * 0.9
    min_thresh = 5
    good_words = Word.objects.filter(lyric__count__gt=min_thresh) \
        .filter(lyric__count__lt=max_thresh).distinct('word')
    logger.info("Number of Good Words: %s" % good_words.count())
    logger.info("Elapsed Time: %s" % (time.time() - start))
    word_to_index = {}
    for index, word in enumerate(good_words):
        word_to_index[word.word] = index
    logger.info("Word To Index Map Created")
    logger.info("Elapsed Time: %s" % (time.time() - start))
    doc_freq = np.zeros(good_words.count())
    for word in good_words:
        doc_freq[word_to_index[word.word]] = word.lyric_set.count() + 1
    logger.info("Doc Freq Matrix Created")
    logger.info("Elapsed Time: %s" % (time.time() - start))
    lyrics = Lyric.objects.all()
    song_word = np.zeros([num_ids, good_words.count()])
    good_lyrics = lyrics.filter(word__in=good_words)
    logger.info("Building Matrix for %s lyrics" % good_lyrics.count())
    logger.info("Elapsed Time: %s" % (time.time() - start))
    for lyric in good_lyrics:
        song_word[lyric.song_id - 1, word_to_index[lyric.word.word]] = float(lyric.count)
    logger.info("Song Word Matrix Created")
    logger.info("Elapsed Time: %s" % (time.time() - start))
    audio_matrix = np.zeros((num_ids, 7))
    audio_features = AudioFeatures.objects.all()
    good_features = ['danceability', 'energy', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence']
    for af in audio_features:
        audio_matrix[af.song_id - 1] = [val for key, val in af if key in good_features]
    logger.info("Audio Features Matrix Created")
    logger.info("Elapsed Time: %s" % (time.time() - start))
    playlist_song = np.zeros((Playlist.objects.all().aggregate(Max('id'))['id__max'], num_ids))
    for playlist in Playlist.objects.all():
        for song in playlist.songs.all():
            playlist_song[playlist.id - 1, song.id - 1] = 1
    logger.info("Playlist Song Matrix Created")
    logger.info("Elapsed Time: %s" % (time.time() - start))
    write_pickles()
    logger.info("Wrote pickle files")
    logger.info("Elapsed Time: %s" % (time.time() - start))

if __name__ == "__main__":
    build_matrices()
    sys.exit(0)
