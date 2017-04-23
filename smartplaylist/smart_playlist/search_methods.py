from smart_playlist import db_builder, text_anal


def search_v1(song, artist):
    song, created = db_builder.build_song_from_name(song, artist)
    if created:
        text_anal.refresh_matrices(song)
        return text_anal.get_cosine_top_songs(song)
    else:
        return text_anal.get_pmi_top_songs(song)


def search_v2(song, artist):
    pass


def search_v3(song, artist):
    pass
