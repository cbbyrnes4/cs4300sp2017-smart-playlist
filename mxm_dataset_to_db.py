#!/usr/bin/env python

"""
Thierry Bertin-Mahieux (2011) Columbia University
tb2332@columbia.edu

This code puts the musiXmatch dataset (format: 2 text files)
into a SQLite database for ease of use.

This is part of the Million Song Dataset project from
LabROSA (Columbia University) and The Echo Nest.
http://labrosa.ee.columbia.edu/millionsong/

Copyright 2011, Thierry Bertin-Mahieux

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sqlite3
import sys


def encode_string(s):
    """
    Simple utility function to make sure a string is proper
    to be used in a SQLite query
    (different than posgtresql, no N to specify unicode)
    EXAMPLE:
      That's my boy! -> 'That''s my boy!'
    """
    return "'" + s.replace("'", "''") + "'"


if __name__ == '__main__':

    # params
    trainf = sys.argv[1]
    testf = sys.argv[2]
    outputf = sys.argv[3]

    # sanity checks
    if not os.path.isfile(trainf):
        print('ERROR: %s does not exist.' % trainf)
        sys.exit(0)
    if not os.path.isfile(testf):
        print('ERROR: %s does not exist.' % testf)
        sys.exit(0)
    if not os.path.isfile(outputf):
        print('ERROR: %s does not exist.' % outputf)
        sys.exit(0)

    # open output SQLite file
    conn = sqlite3.connect(outputf)

    # get words, put them in the words table
    f = open(trainf, 'r')
    topwords = []
    for line in f:
        if line == '':
            continue
        if line[0] == '%':
            topwords = line.strip()[1:].split(',')
            f.close()
            break
    for wid, w in enumerate(topwords):
        q = "INSERT INTO smart_playlist_word VALUES(" + str(wid + 1) + ", " + encode_string(w) + ")"
        conn.execute(q)
    conn.commit()
    # sanity check, make sure the words were entered according
    # to popularity, most popular word should have ROWID 1
    q = "SELECT id, word FROM smart_playlist_word ORDER BY ROWID"
    res = conn.execute(q)
    tmpwords = res.fetchall()
    assert len(tmpwords) == len(topwords), 'Number of words issue.'
    for k in range(len(tmpwords)):
        assert tmpwords[k][0] == k + 1, 'ROWID issue.'
        assert tmpwords[k][1].encode('utf-8') == topwords[k], 'ROWID issue.'
    print("'words' table filled, checked.")

    # we put the train data in the dataset
    f = open(trainf, 'r')
    cnt_lines = 0
    lid = 1
    for line in f:
        if line == '' or line.strip() == '':
            continue
        if line[0] in ('#', '%'):
            continue
        lineparts = line.strip().split(',')
        tid = lineparts[0]
        mxm_tid = lineparts[1]
        for wordcnt in lineparts[2:]:
            wordid, cnt = wordcnt.split(':')
            q = "INSERT INTO smart_playlist_lyric VALUES(" + str(lid) + ", " + str(mxm_tid) + ", " + str(
                cnt) + ", 0, " + str(wordid) + ")"
            conn.execute(q)
            lid += 1
        # verbose
        cnt_lines += 1
        if cnt_lines % 15000 == 0:
            print('Done with %d train tracks.' % cnt_lines)
            conn.commit()
    f.close()
    conn.commit()
    print('Train lyrics added.')

    # we put the test data in the dataset
    # only difference from train: is_test is now 1
    f = open(testf, 'r')
    cnt_lines = 0
    for line in f:
        if line == '' or line.strip() == '':
            continue
        if line[0] in ('#', '%'):
            continue
        lineparts = line.strip().split(',')
        tid = lineparts[0]
        mxm_tid = lineparts[1]
        for wordcnt in lineparts[2:]:
            wordid, cnt = wordcnt.split(':')
            q = "INSERT INTO smart_playlist_lyric VALUES(" + str(lid) + ", " + str(mxm_tid) + ", " + str(
                cnt) + ", 1, " + str(wordid) + ")"
            conn.execute(q)
            lid += 1
        # verbose
        cnt_lines += 1
        if cnt_lines % 15000 == 0:
            print('Done with %d train tracks.' % cnt_lines)
            conn.commit()
    f.close()
    conn.commit()
    print('Test lyrics added.')

    # close output SQLite connection
    conn.close()
