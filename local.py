#!/usr/bin/python3

'''@package local
Beolvassa a sablonokat, helyi függvények.
'''

import os
import sys
import glob
import locale
import yaml
import re
import datetime

locale.setlocale(locale.LC_ALL, 'hu_HU.UTF-8')

global BASE
BASE = os.path.dirname(__file__)
sys.path.append(BASE)

def get_tanevek():
    '''A létező tanéveket (tanev/nnnn könyvtárak) adja vissza: [2014, 2015, ...]'''
    tanevek = glob.glob(BASE + '/tanev/????')
    return [ int(t[-4:]) for t in sorted(tanevek) ]

def get_last_tanev():
    '''A tanev/nnnn könyvtárakból a legutolsó évszámot adja vissza'''
    return get_tanevek()[-1]

def get_tanev():
    '''A naptár szerinti aktuális tanév'''
    return (datetime.date.today() - datetime.timedelta(days=210)).year


# A sablon könyvtárból lehet include-olni pl. így
# P2: !include biz-P2a.ini
def yaml_include(loader, node):
    # return yaml.load(open('%s/%s/%s' % (BASE, 'sablon', node.value)))
    # print('INI:', node.value)
    with open(os.path.join(BASE, 'sablon', node.value)) as inputfile:
        return yaml.load(inputfile)

yaml.add_constructor("!include", yaml_include)

class Sablon(dict):
    def __init__(self, sablonnev, **kwargs):
        self.data = yaml.load(open(os.path.join(BASE, 'sablon', sablonnev+'.ini')))
        self.data['sablonnev'] = sablonnev

        for key in ['om', 'tsz', 'nev', 'osztaly', 'tanev']:
            self.data['P3'][key] = self.data['P3']['bal'][key]
            del(self.data['P3']['bal'][key])

        for key in ['hely', 'ev', 'ho', 'nap', 'tovabb', 'jegyzet']:
            self.data['P3'][key] = self.data['P3']['jobb'][key]
            del(self.data['P3']['jobb'][key])

        # A háttér a "külső" ini-ben van
        self.data['P3']['hatter'] = self.data['P3-hatter']
        del(self.data['P3-hatter'])

        # Ennyi sor van összesen
        self.nRows = len(self.data['P3']['bal']['y']) + len(self.data['P3']['jobb']['y']) + 1

        self.makeTargySorrend(sablonnev)
        self.makeFejlec(sablonnev)

        super(Sablon, self).__init__(self.data)

    def makeTargySorrend(self, sablon):
        '''A "tantargyak.ini"-ből beolvassa a tárgyakhoz tartozó helyeket

        @return <tt>{'irodalom': 1, 'matematika': 6, ...}</tt>
                <tt>{'matek': 'matematika', ...}</tt>
        '''

        self.data['targyHely'], self.data['targyValodiNev'] = {}, {} # sablononként fölsorolva a tárgyHelyek...

        with open(os.path.join(BASE, 'tantargyak.ini')) as f:
            self.tantargyak = yaml.load(f)

        oszlop = self.tantargyak['helyek'][sablon]

        self.data['targyHely'], self.data['targyValodiNev'] = {}, {}
        for t in self.tantargyak['targyak']:
            nevek, hely = t['nevek'], t['hely'][oszlop]
            # egy tárgyhoz tartozhat több név is, ezeket vesszük sorra
            # közülük az elsőt írjuk a bizonyítványba: data['targyValodiNev'][targy álnév] -> tárgy valódi neve
            targyNev = nevek[0]
            self.data['targyHely'][targyNev] = hely
            self.data['targyValodiNev'][targyNev] = targyNev
            for targyAlnev in nevek[1:]:
                self.data['targyValodiNev'][targyAlnev] = targyNev

    def makeFejlec(self, sablon):
        '''A fejléc mezők neveit generálja

        @param sablon a sablon neve, amihez kell a fejléc
        @return fejlec
            - fejlec: ['sablon', 'uid', 'osztaly', ... 't15', 'o15', 'j15', ... 'tovabb', 'jegyzet', ...]
        '''
        fejlec = ['sablon', 'uid', 'osztaly', 'nev', 'szulhely', 'szulido', 'pnev', 'mnev', 'khely', 'kev', 'kho', 'knap', 'om', 'tsz', 'tanev',
                    'tovabb', 'jegyzet', 'hely', 'ev', 'ho', 'nap'
                 ]
        for i in range(1, self.nRows):
            fejlec.extend([ 't%02d' % i, 'o%02d' % i, 'j%02d' % i ])

        self.data['fejlec'] = fejlec

class sablonok(dict):
    def __init__(self, **kwargs):
        data = {}
        for sablon in glob.glob(BASE + '/sablon/*-[A-Z]*.ini'):
            sablonnev = os.path.basename(sablon)[:-4]
            sablon_file = os.path.join(BASE, 'sablon', sablonnev + '.ini')
            if not os.path.isfile(sablon_file):
                continue
            data[sablonnev] = Sablon(sablonnev)

        super(sablonok, self).__init__(data)

if __name__ == "__main__":
    i = sablonok()
    pass

    #a = Sablon('45-B')
    #print(a)
#    print(get_last_tanev())

