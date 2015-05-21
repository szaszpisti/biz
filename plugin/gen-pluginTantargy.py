#!/usr/bin/python3
# -*- coding: utf8 -*-

import sys, csv
#filename = sys.argv[0].split('/')[-1][4:]

jegy = {'1': 'elégtelen', '2': 'elégséges', '3': 'közepes', '4': 'jó', '5': 'jeles'}

OV = {}
OVuid = ['tmp'] # Ez a segédtömb csak a sorrend végett van (dict-ben elvész a sorrend)
OVout = []
OVjegy_reader = csv.reader(open('TanVizsgaEditPeda.csv'), delimiter='\t', quoting=csv.QUOTE_MINIMAL)
next(OVjegy_reader) # van fejléc
for sor in OVjegy_reader:
    # Ha új uid (az előző nem ez volt):
    if OVuid[-1] != sor[13]: OVuid.append(sor[13])
    if sor[7] == 'Évvégi':
        if not sor[13] in OV: OV[sor[13]] = []
        OV[sor[13]].extend([sor[2], jegy[sor[8]], sor[0]])
del(OVuid[0]) # Az első ("tmp") törlése

for uid in OVuid:
    targy, jegy, nev = OV[uid][:3]
    OVout.append("        '%s': ['%s', '%s', '---'" % (uid, targy, jegy))
    del(OV[uid][:3])
    while OV[uid]:
        targy, jegy, nev = OV[uid][:3]
        OVout[-1] += ","
        OVout.append("                        '%s', '%s', '---'" % (targy, jegy))
        del(OV[uid][:3])
    OVout[-1] += "],  # %s" % nev

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
    if diak['uid'] == '79088302529': # Rózsa Bence Attila 12b
        self.targyValodiNev['belügyi rendészeti ismeretek'] = 'belügyi rendészeti ismeretek'
        self.targyHely['belügyi rendészeti ismeretek'] = 'f'
        sor[-8:-8] = ['Belügyi rendészeti ismeretek', 'jó', '---']

# HORVÁTH Mártonnak van írva...
if diak['uid'] == '75455330219':
    diak['nev'] = 'Horváth Márton'
''' % '\n'.join(OVout)

print(out, file=open('pluginTantargy.py', 'w'))
