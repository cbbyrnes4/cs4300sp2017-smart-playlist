from django.conf.urls import url

from smart_playlist import views

app_name = 'sp'
urlpatterns = [
    url(r'^$', views.search, name="search"),
    url(r'^find_song/$', views.find_song, name='find_song'),
    url(r'^find_artist/$', views.find_artist, name='find_artist')
]