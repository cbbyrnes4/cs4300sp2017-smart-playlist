from django.db import models


# Create your models here.


class Word(models.Model):
    word = models.CharField(max_length=200)


class Lyric(models.Model):
    mxm_tid = models.IntegerField()
    word = models.ForeignKey(Word)
    count = models.IntegerField()
    is_test = models.IntegerField()


class Artist(models.Model):
    name = models.CharField(max_length=200)
    spotify_id = models.CharField(max_length=30)


class Song(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ManyToManyField(Artist)
    mxm_tid = models.IntegerField()
    spotify_id = models.CharField(max_length=30)


class AudioFeatures(models.Model):
    song = models.ForeignKey(Song)
