import cPickle as pickle
import logging
import os
import time

import numpy as np
from django.db.models import Max

from smart_playlist.models import Lyric, Song, Word

song_count = -1
doc_freq = np.array([])
song_word = np.array([])
good_words = None
word_to_index = {}
initialized = False
init_start = 0
logger = logging.getLogger(__name__)

doc_freq_pickle = "/usr/src/app/pickles/doc_freq.pickle"
song_word_pickle = '/usr/src/app/pickles/song_word.pickle'
good_words_pickle = '/usr/src/app/pickles/good_words.pickle'
word_to_index_pickle = '/usr/src/app/pickles/word_to_index.pickle'


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


def get_top_songs(song):
    overlap = get_lyrically_overlapping_songs(song)
    cos_sims = calc_cosine_sims(song, overlap)
    top_indices = np.argsort(cos_sims)[::-1][-min(len(cos_sims), 15):]
    return [(Song.objects.get(id=overlap[i]['song_id']), cos_sims[i]) for i in top_indices]


def calc_cosine_sims(song, overlapping_songs):
    song_tf = np.zeros(Word.objects.count())
    for lyric in song.lyric_set.all():
        try:
            df = doc_freq[lyric.word.id-1]
        except IndexError:
            df = 1
        song_tf[lyric.word_id-1] = float(lyric.count) * np.log(song_count / df)
    cos_sims = np.zeros(len(overlapping_songs))
    for ind, olap in enumerate(overlapping_songs):
        cos_sims[ind] = cosine_sim(song_tf, olap)
    return cos_sims


def cosine_sim(q, d):
    song_vec = tfidf_vec(d['song_id'])
    song_vec = np.append(song_vec, np.zeros(len(q)-len(song_vec)))
    return np.dot(q, song_vec) / (np.linalg.norm(q) * np.linalg.norm(song_vec))


def tfidf_vec(song_id):
    return song_word[song_id - 1] * np.log(song_count / doc_freq)


def build_matrices():
    # TODO: Make more efficient
    global song_count, doc_freq, song_word, good_words, word_to_index, initialized, init_start
    init_start = time.time()
    song_count = Song.objects.count()
    logger.info("Songs: %s" % song_count)
    logger.info("Total Number of Words %s" % Word.objects.count())
    if os.path.exists(good_words_pickle):
        with open(good_words_pickle, 'rb') as f:
            good_words = pickle.load(f)
    else:
        max_thresh = song_count * 0.9
        min_thresh = 10
        good_words = Word.objects.filter(lyric__count__gt=min_thresh)\
            .filter(lyric__count__lt=max_thresh).distinct('word')
    logger.info("Number of Good Words: %s" % good_words.count())
    if os.path.exists(word_to_index_pickle):
        with open(word_to_index_pickle, 'rb') as f:
            word_to_index = pickle.load(f)
    else:
        for index, word in enumerate(good_words):
            word_to_index[word.word] = index
    logger.info("Word To Index Map Created")
    if os.path.exists(doc_freq_pickle):
        with open(doc_freq_pickle, 'rb') as f:
            doc_freq = pickle.load(f)
    else:
        doc_freq = np.zeros(good_words.count())
        for word in good_words:
            doc_freq[word_to_index[word.word]] = word.lyric_set.count() + 1
    logger.info("Doc Freq Matrix Created")
    if os.path.exists(song_word_pickle):
        with open(song_word_pickle, 'rb') as f:
            song_word = pickle.load(f)
    else:
        lyrics = Lyric.objects.all()
        song_word = np.zeros([Song.objects.all().aggregate(Max('id'))['id__max'], good_words.count()])
        good_lyrics = lyrics.filter(word__in=good_words)
        logger.info("Building Matrix for %s lyrics" % good_lyrics.count())
        for lyric in good_lyrics:
            song_word[lyric.song_id - 1, word_to_index[lyric.word.word]] = float(lyric.count)
    logger.info("Song Word Matrix Created")
    end = time.time()
    logger.info("Elapsed time: %s" % (end - init_start))
    write_pickles()
    initialized = True


def write_pickles():
    with open(doc_freq_pickle, 'wb') as f:
        pickle.dump(doc_freq, f)
    with open(song_word_pickle, 'wb') as f:
        pickle.dump(song_word, f)
    with open(good_words_pickle, 'wb') as f:
        pickle.dump(good_words, f)
    with open(word_to_index_pickle, 'wb') as f:
        pickle.dump(word_to_index, f)


def refresh_matrices(song):
    # TODO: Make more efficient
    pass
