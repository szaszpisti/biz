#!/usr/bin/python3

'''
A diák adataihoz beírja:
- az osztályzóvizsgás záradékokat,
- a TESZI-s óraszámokból készített záradékot
'''

import sys, csv
import xlrd
from datetime import datetime, timedelta

year = (datetime.now() - timedelta(days=210)).year
tanev = '%d-%d' % (year, year-1999)

jegy = {'1': 'elégtelen', '2': 'elégséges', '3': 'közepes', '4': 'jó', '5': 'jeles'}

# Több évfolyamnyi záradék is megtalálható, ezeket külön, az "uid-evfolyam" kulcsokhoz pakoljuk
# zaradek = { '01234567890-11': ['elso záradék', 'második záradék'], ... }

zaradek = {}
zaradekFile = xlrd.open_workbook('TanEvvzaradekEdit.xls').sheet_by_index(0)
head = zaradekFile.row_values(0)

for i in range(1, zaradekFile.nrows):
    sor = dict(zip(head, zaradekFile.row_values(i)))
    # csak az OV érdekel
    if sor['Záradék sorszáma'] != 'OV':
        continue
    try:
        # záradék == '... a 12. évfolyamon ...' => '12'
        i = sor['Záradék szövege'].index('. évfolyam')
        evfolyam = sor['Záradék szövege'][i-2:i].strip()
        uid = '%s-%s' % (sor['Tanuló - Közoktatási azonosító'], evfolyam)

        if not uid in zaradek: zaradek[uid] = []
        zaradek[uid].append(sor['Záradék szövege'])
    except:
        print(sor['Tanuló - Név'], sor['Záradék szövege'])

tesziFile = xlrd.open_workbook('teszi-%s.xls' % tanev).sheet_by_index(0)
head = tesziFile.row_values(0)

# minden mezőt stringgé alakítunk
def string(i):
    if type(i) == str: return i
    else: return str(int(i))

for i in range(1, tesziFile.nrows):
    sor = dict(zip(head, [string(i) for i in tesziFile.row_values(i)]))
    if sor['ora'] in ['', 'ora']:
        continue
    evfolyam = sor['osztaly'].split('.')[0]
    uid = '%s-%s' % (sor['uid'], evfolyam)
    if not uid in zaradek: zaradek[uid] = []
    zaradek[uid].append(sor['ora'] + ' óra közösségi szolgálatot teljesített.')

out = []
for uid in sorted(zaradek.keys()):
    out.append("        '%s': %s," % (uid, repr(zaradek[uid])))

zaradekOut = '''
# EZT NE SZERKESZD! - a gen-plugin* generálja

zaradek = {
%s
}

uid = '%%s-%%s' %% (diak['uid'], diak['evfolyam'])
if uid in zaradek:
    if diak['jegyzet']:
        diak['jegyzet'] = '<br /><br />'.join([diak['jegyzet']] + zaradek[uid])
    else:
        diak['jegyzet'] = '<br /><br />'.join(zaradek[uid])
''' % '\n'.join(out)

print(zaradekOut, file=open('pluginDiak.py', 'w'))

