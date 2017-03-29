import matplotlib.pyplot as plt
import django

django.setup()

from django.db.models import Count, Sum

from smart_playlist.models import Lyric


fig = plt.figure()
fig.subplots_adjust(hspace=1)
wps = fig.add_subplot(211)

words_per_song = [x['count'] for x in Lyric.objects.values('mxm_tid').order_by('mxm_tid').
    annotate(count=Count('mxm_tid')).values('count')]

wps.hist(words_per_song, bins=200)

wps.set_xlabel("Words Per Song")
wps.set_title("Histogram of Unique Words Per Song")

wh = fig.add_subplot(212)
words = [x['count'] for x in Lyric.objects.values('word').order_by('word').
    annotate(count=Sum('word')).values('count').order_by('count')]
wh.hist(words, bins=200)
wh.set_xlabel("Occurrences of Words")
wh.set_title("Histogram of Occurrences of Words")

plt.show()