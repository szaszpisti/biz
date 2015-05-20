#!/usr/bin/python3

'''
A diák adataihoz beírja:
- az osztályzóvizsgás záradékokat,
- a TESZI-s óraszámokból készített záradékot
'''

import sys, csv
filename = sys.argv[0].split('/')[-1][4:]

jegy = {'1': 'elégtelen', '2': 'elégséges', '3': 'közepes', '4': 'jó', '5': 'jeles'}

# Több évfolyamnyi záradék is megtalálható, ezeket külön, az "uid-evfolyam" kulcsokhoz pakoljuk
# zaradek = { '01234567890-11': ['elso záradék', 'második záradék'], ... }

zaradek = {}
zaradek_reader = csv.reader(open('TanEvvzaradekEdit.csv'), delimiter='\t', quoting=csv.QUOTE_MINIMAL)
for sor in zaradek_reader:
    if sor[3] != 'OV': continue  # csak az osztályzóvizsgások érdekelnek
    try:
        i = sor[9].index('. évfolyam')
        evfolyam = sor[9][i-2:i].strip()
        uid = '%s-%s' % (sor[1], evfolyam)
        if not uid in zaradek: zaradek[uid] = []
        zaradek[uid].append(sor[9])
    except:
        print(sor[0], sor[9])

teszi_reader = csv.reader(open('teszi.csv'), delimiter='\t', quoting=csv.QUOTE_MINIMAL)
for sor in teszi_reader:
    if sor[3] == '' or sor[3] == 'ora': continue
    evfolyam = sor[1].split('.')[0]
    uid = '%s-%s' % (sor[0], evfolyam)
    if not uid in zaradek: zaradek[uid] = []
    zaradek[uid].append(sor[3] + ' óra közösségi szolgálatot teljesített.')

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

# a 9. B osztálynak valamiért csak 111 óra van beírva, de 185 kell.
if diak['osztaly'] == '9. B':
    diak['o17'] = '185'

# a 9.A osztály 2 órában tanulta az informatikát, de csak 1 van beírva.
if diak['osztaly'] == '9. A':
    diak['o08'] = '74'
''' % '\n'.join(out)

print(zaradekOut, file=open('pluginDiak.py', 'w'))

