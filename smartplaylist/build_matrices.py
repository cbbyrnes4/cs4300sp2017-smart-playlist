import cPickle as pickle
import logging
import sys
import time

import django
import numpy as np
from django.db.models import Max

django.setup()

from smart_playlist import text_anal
from smart_playlist.models import Song, Word, Lyric

logger = logging.getLogger(__name__)


def write_pickles():
    with open(text_anal.doc_freq_pickle, 'wb') as f:
        pickle.dump(doc_freq, f)
    with open(text_anal.song_word_pickle, 'wb') as f:
        pickle.dump(song_word, f)
    with open(text_anal.good_words_pickle, 'wb') as f:
        pickle.dump(good_words, f)
    with open(text_anal.word_to_index_pickle, 'wb') as f:
        pickle.dump(word_to_index, f)
    with open(text_anal.pmi_pickle, 'wb') as f:
        pickle.dump(pmi, f)


if __name__ == "__main__":
    # TODO: Make more efficient
    logger.info("Starting Debug Trace")
    # pydevd.settrace("192.168.1.128", port=3000)
    start = time.time()
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
    song_word = np.zeros([Song.objects.all().aggregate(Max('id'))['id__max'], good_words.count()])
    good_lyrics = lyrics.filter(word__in=good_words)
    logger.info("Building Matrix for %s lyrics" % good_lyrics.count())
    logger.info("Elapsed Time: %s" % (time.time() - start))
    for lyric in good_lyrics:
        song_word[lyric.song_id - 1, word_to_index[lyric.word.word]] = float(lyric.count)
    logger.info("Song Word Matrix Created")
    logger.info("Elapsed Time: %s" % (time.time() - start))
    tfidf_mat = song_word * np.log(song_count / doc_freq)
    pmi = np.dot(tfidf_mat, tfidf_mat.T)
    logger.info("Created PMI Matrix")
    logger.info("Elapsed Time: %s" % (time.time() - start))
    write_pickles()
    logger.info("Wrote pickle files")
    logger.info("Elapsed Time: %s" % (time.time() - start))
    sys.exit(1)
