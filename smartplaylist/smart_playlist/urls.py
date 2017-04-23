from django.conf.urls import url

from smart_playlist import views

app_name = 'sp'
urlpatterns = [
    url(r'(?P<version>[0-9])/$', views.search, name="search"),
]