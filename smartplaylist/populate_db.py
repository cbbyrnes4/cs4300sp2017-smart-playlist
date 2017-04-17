import spotipy
import smart_playlist.db_builder as db_builder
import django

from spotipy import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials

if __name__ == '__main__':
	spotify_key = 'd305abf923f54ff0b2bee3ae17af289d'
	spotify_secret = '55b73d4d03a44a309973c0693edbeaf9'

	spo_cred_manager = SpotifyClientCredentials(spotify_key, spotify_secret)
	sp = spotipy.Spotify(client_credentials_manager=spo_cred_manager)

	for category in sp.categories(limit=50)['categories']['items']:
		db_builder.fetch_category_playlists(category['id'])
