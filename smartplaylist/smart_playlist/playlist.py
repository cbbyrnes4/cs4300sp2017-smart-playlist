from smart_playlist import matrices


def playlist_pmi(song_id):
    return {i + 1: (matrices.playlist_concurrence[song_id - 1, i] /
                    (matrices.playlist_norm[song_id - 1] * matrices.playlist_norm[i] + 1))
            for i in range(matrices.playlist_concurrence.shape[0])
            if matrices.playlist_concurrence[song_id - 1, i] > 0}
