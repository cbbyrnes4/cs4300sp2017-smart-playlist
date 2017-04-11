from django.db import models


# Create your models here.
class Artist(models.Model):
    name = models.CharField(max_length=200)
    mxm_id = models.IntegerField(unique=True)
    spotify_id = models.CharField(max_length=30, null=True)


class Album(models.Model):
    name = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist)
    mxm_id = models.IntegerField(unique=True)
    spotify_id = models.CharField(max_length=30, null=True)


class Song(models.Model):
    name = models.CharField(max_length=200)
    artist = models.ManyToManyField(Artist)
    album = models.ForeignKey(Album)
    mxm_tid = models.IntegerField(unique=True)
    spotify_id = models.CharField(max_length=30, null=True)


class AudioFeatures(models.Model):
    song = models.ForeignKey(Song)
    danceability = models.FloatFields()
    energy = models.FloatFields()
    key = models.IntegerField(unique=True)
    loudness = models.FloatFields()
    mode = models.IntegerField(unique=True)
    speechiness = models.FloatFields()
    acousticness = models.FloatFields()
    instrumentalness = models.FloatFields()
    liveness = models.FloatFields()
    valence = models.FloatFields()
    tempo =models.FloatFields()
    duration_ms = models.IntegerField(unique=True)
    time_signature = models.IntegerField(unique=True)


class Word(models.Model):
    word = models.CharField(max_length=200)


class Lyric(models.Model):
    song = models.ForeignKey(Song, null=True)
    mxm_id = models.IntegerField()
    word = models.ForeignKey(Word)
    count = models.IntegerField()
    is_test = models.IntegerField()


