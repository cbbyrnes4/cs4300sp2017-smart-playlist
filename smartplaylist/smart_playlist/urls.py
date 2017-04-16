from django.conf.urls import url

from smart_playlist import views

app_name = 'sp'
urlpatterns = [
    url(r'search/$', views.search, name="search"),
]