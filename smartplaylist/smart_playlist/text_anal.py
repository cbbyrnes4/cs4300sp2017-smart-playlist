import numpy as np

from smart_playlist.models import Lyric, Song, Word


def build_df_matrix():
    """
    Returns the 
    :return: 
    """
    df = np.zeros(Word.objects.count())
    for word in Word.objects.all():
        df[word.id - 1] = word.lyric_set.count() + 1
    return df


def build_song_term_matrix(song_count, doc_freq):
    """
    Builds the song-term matrix from the lyrics data in the database
    mat[i, j] is the count of word j-1 in song i-1
    :return: song-term matrix
    """
    lyrics = Lyric.objects.all()
    mat = np.zeros([Song.objects.count(), Word.objects.count()])
    for lyric in lyrics:
        mat[lyric.song_id - 1, lyric.word_id - 1] = float(lyric.count) * np.log(
            song_count / doc_freq[lyric.word_id - 1])
    return mat


song_count = Song.objects.count() + 1
doc_freq = build_df_matrix()
song_word = build_song_term_matrix(song_count, doc_freq)


def get_lyrically_overlapping_songs(song):
    """
    Returns all of the song ids of songs that share a lyric with the provided song
    :param song: song to match with (Song)
    :return: set of song ids
    """
    song_words = Lyric.objects.filter(song=song).values('word').distinct()
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
    song_vec = song_word[d['song_id'] - 1]
    song_vec = np.append(song_vec, np.zeros(len(q)-len(song_vec)))
    return np.dot(q, song_vec) / (np.linalg.norm(q) * np.linalg.norm(song_vec))


def refresh_matrices():
    global song_count
    song_count = Song.objects.count() + 1
    global doc_freq
    doc_freq = build_df_matrix()
    global song_word
    song_word = build_song_term_matrix(song_count, doc_freq)
