from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


# Create your models here.
class Artist(models.Model):
    name = models.CharField(max_length=200)
    mxm_id = models.IntegerField(unique=True, null=True)
    spotify_id = models.CharField(unique=True, max_length=30, null=True)

    def __str__(self):
        return self.name


class Album(models.Model):
    name = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist)
    mxm_id = models.IntegerField(unique=True, null=True)
    spotify_id = models.CharField(unique=True, max_length=30, null=True)


class Song(models.Model):
    name = models.CharField(max_length=200)
    artist = models.ManyToManyField(Artist)
    album = models.ForeignKey(Album)
    mxm_tid = models.IntegerField(unique=True, null=True, db_index=True)
    spotify_id = models.CharField(max_length=30, null=True, unique=True, db_index=True)

    def __str__(self):
        return '%s by: %s' % (self.name, ', '.join(a.name for a in self.artist.all()))


class AudioFeatures(models.Model):
    song = models.ForeignKey(Song)
    danceability = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    energy = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    key = models.IntegerField(choices=((0, "C"), (1, 'C#'), (2, 'D'), (3, 'D#'), (4, 'E'), (5, 'F'), (6, 'F#')
                                       , (7, 'G'), (8, 'G#'), (9, 'A'), (10, 'A#'), (11, 'B')))
    loudness = models.FloatField()
    mode = models.IntegerField(choices=((0, "Major"), (1, 'Minor')))
    speechiness = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    acousticness = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    instrumentalness = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    liveness = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    valence = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    tempo = models.FloatField()
    duration_ms = models.IntegerField()
    time_signature = models.IntegerField()


class Word(models.Model):
    word = models.CharField(max_length=200)


class Lyric(models.Model):
    song = models.ForeignKey(Song, null=True, db_index=True)
    mxm_id = models.IntegerField()
    word = models.ForeignKey(Word, db_index=True)
    count = models.IntegerField()
    is_test = models.IntegerField()

    def __str__(self):
        return '%s: (%s, %s)' % (self.song.name, self.word.word, self.count)


class Playlist(models.Model):
    name = models.CharField(max_length=255)
    spotify_id = models.CharField(max_length=30, unique=True)
    songs = models.ManyToManyField(Song)
