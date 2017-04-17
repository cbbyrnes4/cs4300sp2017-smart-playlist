from __future__ import unicode_literals

from django.apps import AppConfig
import text_anal


class SmartPlaylistConfig(AppConfig):
    name = 'smart_playlist'

    def ready(self):
        text_anal.refresh_matrices()