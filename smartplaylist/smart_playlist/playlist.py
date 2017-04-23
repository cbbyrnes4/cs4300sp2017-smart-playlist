import numpy as np

from smart_playlist import matrices


def playlist_pmi(song_id):
    top_indices = np.argsort(matrices.playlist_concurrence[song_id - 1])[::-1]
    return {i + 1: matrices.playlist_concurrence[song_id - 1][i]
            for i in top_indices if matrices.playlist_concurrence[song_id - 1][i] > 0}
