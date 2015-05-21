#!/usr/bin/python3

import sys, csv
import xlrd
from datetime import datetime, timedelta

year = (datetime.now() - timedelta(days=210)).year
tanev = '%d-%d' % (year, year-1999)
jegy_nev = {'1': 'elégtelen', '2': 'elégséges', '3': 'közepes', '4': 'jó', '5': 'jeles'}

# minden mezőt stringgé alakítunk
def string(i):
    if type(i) == str:
        return i
    else:
        return str(int(i))

OV = {}
OVuid = [] # Ez a segédtömb csak a sorrend végett van (dict-ben elvész a sorrend)
OVout = []

OVjegyFile = xlrd.open_workbook('TanVizsgaEditPeda.xls').sheet_by_index(0)
head = OVjegyFile.row_values(0)

uids = [] # itt lesz az eredeti sorrendben az egyedi uid: ['uid1', 'uid2', ...]
OV = {}   # az OV bejegyzések uid szerint: {'uid1': [["'Angol nyelv', 'jó', '---',", 'nev1'], ["..."]], 'uid2': ...}

for i in range(1, OVjegyFile.nrows):
    sor = dict(zip(head, [string(i) for i in OVjegyFile.row_values(i)]))
    if sor['Értékelés tipusa'] != 'Évvégi':
        continue

    uid = sor['Közoktatási azonosító']

    if uid not in uids: uids.append(uid)
    targy_sor = "'%s', '%s', '---'" % (sor['Tantárgy - Tantárgy neve'], jegy_nev[sor['Eredmény']])
    nev = sor['Tanuló neve']

    if uid not in OV:
        OV[uid] = []
    OV[uid].append([targy_sor, sor['Tanuló neve']])

OV_out = []
for uid in uids:
    # Az uid utolsó bejegyzése: ["'Angol nyelv', 'jó', '---'", ...] => ["'Angol nyelv', 'jó', '---'],    # Név", ...]
    OV[uid][-1][0] = '%-35s  # %s' % (OV[uid][-1][0] + '],', OV[uid][-1][1])
    OV_out.append("        '%s': [" % uid \
        + ",\n                        ".join(t[0] for t in OV[uid]) \
    )

out = '''
# EZT NE SZERKESZD! - a gen-plugin* generálja
# Ügyeljünk arra, hogy a "sor" változót ne hozzuk létre újra (pl. sor = sor + [...])!
# Mivel minden diáknál végrehajtja, ügyeljünk, hogy ne nagyon legyen fájlművelet!

OV = {
%s
}
if diak['uid'] in OV:
    sor[-8:-8] = OV[diak['uid']]

# Ez nincs benne a tantárgylistában, bele kell csempészni.
if diak['ev'] == '2015':
    pass
#    if diak['uid'] == '79088302529': # Rózsa Bence Attila 12b
#        self.targyValodiNev['belügyi rendészeti ismeretek'] = 'belügyi rendészeti ismeretek'
#        self.targyHely['belügyi rendészeti ismeretek'] = 'f'
#        sor[-8:-8] = ['Belügyi rendészeti ismeretek', 'jó', '---']


# HORVÁTH Mártonnak van írva... 2015-ig kell
if diak['uid'] == '75455330219':
    diak['nev'] = 'Horváth Márton'
''' % '\n'.join(OV_out)

print(out, file=open('pluginTantargy.py', 'w'))
