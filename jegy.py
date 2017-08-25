#!/usr/bin/python3

'''@package jegy
Lefuttatva feldolgozza a "tanev/nnnn" könyvtárban található bizonyitvany-tanev-oszt.csv fájlokat,
mindegyikhez elkészíti az oszt.csv-t, ami a nyomtatás input formátumában van.
'''
# python-yaml

import sys
import csv
import os.path
import yaml
import locale
import re, glob
import datetime

global BASE
BASE = os.path.dirname(__file__)
sys.path.append(BASE)

import local

locale.setlocale(locale.LC_ALL, 'hu_HU.UTF-8')

sablonok = local.sablonok()

def main():
    '''Főprogram'''

    if len(sys.argv) > 1 and len(sys.argv[1]) == 4:
        ev = int(sys.argv[1])
        del(sys.argv[1])
    else:
        ev = local.get_last_tanev()

    osztalyok = [oszt for oszt, _, _, _, _ in getOsztalyLista(ev).lista]
    if len(sys.argv) > 1:
        osztalyok = sys.argv[1:]

    for oszt in sorted(osztalyok):
        print(oszt, end=' ', flush=True)
        t = Bizonyitvany(ev, oszt, quiet=True)
    print()

class getOsztalyLista():
    '''A forrás könyvtárban található összes csv-t végigveszi,
    a fájlnevek alapján elkészíti belőle az osztálylistát, a hozzá tartozó sablonnevekkel
    '''
    def __init__(self, ev):
        '''
                  osztályID, osztályNév, évfolyam, sablon
        lista: [ ['10b',     '10. B',    10,       'felso'],   ...]
        '''
        self.ev = ev
        self.config = yaml.load(open(os.path.join(BASE, 'tanev', str(self.ev), 'biz.ini'))) 

        ## az osztályok listája a következő formában:
        #           osztályID, osztályNév, évfolyam, felső-e
        # lista: [ ['10b',     '10. B',    10,       True],   ...]
        self.lista = []

        # vesszük a forrás könyvtárban található összes csv-t
        csvFiles = glob.glob(os.path.join(BASE, 'tanev', str(self.ev), 'bizonyitvany-%d-*.csv' % self.ev))

        for csvFile in csvFiles:
            f = os.path.basename(csvFile) # basename
            oszt = f[:f.rfind('.')].replace('bizonyitvany-%d-' % ev, '') # levágjuk az elejét és a kiterjesztést
            self.lista.append(self.Osztaly(oszt))

        # rendezzük az osztálylistát évfolyam(2), majd név(1) alapján
        self.lista.sort(key=lambda x: 10*x[2] + ord(x[3]))
        if len(self.lista) == 0:
            self.lista = [['12b', '12. B', 12, 'B', '4oszt']]

    def Osztaly(self, oszt):
        '''A paraméterként kapott osztálynevet dolgozza fel

        @param oszt: a feldolgozandó osztályazonosító ("10b")

        @return <tt>['10b', '10. B', 10, 'B', '4oszt']</tt>
        '''
        evfolyam = int(oszt[:-1])
        ab = oszt[-1].upper()
        evf = self.ev + (12-evfolyam) - 2000
        if evf < 0:
            evf = evf + 100
        oid = 'd%02d%s' % (evf, ab.lower())

        osztaly = '%d. %s' % (evfolyam, ab)

        return [oszt, osztaly, evfolyam, ab, oid]

class Bizonyitvany():
    def __init__(self, ev, oszt, quiet=False):
        '''Egy osztályhoz tartozó bizonyítványok

        @param oszt osztályazonosító
        @param quiet ne kérdezze meg a bukásokat -> 4 bukásra automatikusan évismétlést ír be
        '''

        global BASE
        self.BASE = BASE
        self.ev = ev

        ## osztályazonosító
        self.oszt = oszt
        self.bizOsztaly = {}

        oszt, osztaly, evfolyam, ab, oid = getOsztalyLista(self.ev).Osztaly(oszt)

        self.config = self.getConfig(evfolyam)
        self.config.update({ 'osztaly': osztaly, 'evfolyam': evfolyam })
        osztalySablon = self.configAll['tip'][oid]

        self.bizFile = os.path.join(BASE, 'tanev', str(self.ev), 'bizonyitvany-%d-%s.csv' % (self.ev, oszt))
        self.csvFile = os.path.join(BASE, 'tanev', str(self.ev), '%s.csv' % oszt)

        # Ha nincs még csv vagy régebbi a forrásnál, akkor generálni kell
        if not os.path.isfile(self.csvFile) or os.path.getmtime(self.csvFile) < os.path.getmtime(self.bizFile):

            print('\n   Nincs csv, elkészítem: %s' % self.csvFile)

            osztalyFile = csv.reader(open(self.bizFile), delimiter='\t', quoting=csv.QUOTE_MINIMAL)
            head = next(osztalyFile)

            for sor in osztalyFile:

                # d: a bizonyítvány egy sora
                d = dict(list(zip(head, sor)))

                if d['tsz'] == '':
                    print('Nincs törzslapszám: %s %5s %s' % (d['uid'], d['osztaly'], d['nev']))
                if not d['igazolt']:
                    print('   *** %s (%s): hiányos a bizonyítványa, átugrom.' % (d['nev'], oszt))
                    continue

                # az osztály alapértelmezett sablonja
                sablon = osztalySablon
                # Ha az ini-ben van az uid-hez megadott sablonnév, azt haszználjuk
                uid = d['uid']
                if uid in self.configAll['tip']:
                    sablon = self.configAll['tip'][uid]

                if not sablon[0] == '4': # ha 6-8 stb. kezdetű sablonnév, akkor van -alsó és -felső is
                    if evfolyam < 9:
                        sablon += '-also'
                    else:
                        sablon += '-felso'

                diak = Diak(d, head, sablonok[sablon], self.config, self.configAll['maxDicseret']).adatok
                self.bizOsztaly[uid] = diak

            self.nevsor, self.nevsorById = self.makeNevsor()
            self.csvOut()

        else:
            # Már megvan a csv, lehet beolvasni.
            with open(self.csvFile) as csvfile:
                biz_reader = csv.reader(csvfile, delimiter='\t', quoting=csv.QUOTE_MINIMAL, lineterminator=os.linesep)

                sablon_fejlec = next(biz_reader)
                if sablon_fejlec[0] != 'sablon':
                    csvfile.seek(0) # nem volt fejléc, visszaállítjuk az olvasást a fájl elejére
                    sablon_fejlec = False

                for sor in biz_reader:
                    try:
                        sablon = sablonok[sor[0]]
                    except:
                        # print(sablonok)
                        print(sablonok.keys())
                        exit()

                    # Ha régi típusú bizonyítvány, annak a fejlécét használjuk
                    if sablon_fejlec:
                        sablon['fejlec'] = sablon_fejlec

                    diak = dict(list(zip(sablon['fejlec'], sor)))

                    self.bizOsztaly[diak['uid']] = diak

            self.nevsor, self.nevsorById = self.makeNevsor()

    def getConfig(self, evfolyam):
        '''Beolvassa a config fájlt (biz.ini)

        @param evfolyam ez alapján veszi a normál vagy végzős dátumot

        @return a konfigurációs fájlból vett és a számított beállítások szótára
        '''
        from os.path import join

        configAll = yaml.load(open(join(self.BASE, 'tanev', str(self.ev), 'biz.ini')))

        config = {'evfolyam': evfolyam}
        config['kev'], config['kho'], config['knap'] = re.compile("[\. ]+").split(configAll['beiratkozasDate'])
        if evfolyam >= 12:
            bizDate = configAll['vegzosDate']
        else:
            bizDate = configAll['bizDate']

        config['ev'], config['ho'], config['nap'] = re.compile("[\. ]+").split(bizDate)
        config['tanev'] = '%s  %s' % (int(config['ev'])-1,  config['ev'])

        self.configAll = configAll.copy()
        self.configAll['tip'] = {}
        for k, v in configAll['tip'].items():
            self.configAll['tip'][str(k)] = v

        return config

    def makeNevsor(self):
        '''A bizOsztaly-ból névsort készít

        @return nevsor, nevsorById
           - nevsor: <tt>['Alma Attila', 'Baka Béla', ...]</tt>
           - nevsorById: <tt>[['Alma Attila', '123456789'], ['Baka Béla', '987654321'], ...]</tt>
        '''
        nevsorById = []
        for uid in list(self.bizOsztaly.keys()):
            nevsorById.append ([self.bizOsztaly[uid]['nev'], uid])

        # sort = lambda x, y: locale.strcoll(x[0], y[0])
        # nevsorById.sort(cmp=sort)
        nevsorById.sort(key=lambda x: locale.strxfrm(x[0]))

        nevsor = [ nev[0] for nev in nevsorById ]
        return nevsor, nevsorById

    def csvOut(self):
        '''Fájlba írja a csv-t
        '''
        jegy_writer = csv.writer(open(self.csvFile, 'w'), delimiter='\t', lineterminator=os.linesep)

        for nev, uid in self.nevsorById:
            diak = self.bizOsztaly[uid]

            # Ha van extra módosítási igény, azt az "config['pluginDiak']" fájlba tesszük
#            if 'pluginDiak' in self.configAll:
#                exec(open(os.path.join(BASE, 'plugin', self.configAll['pluginDiak'])).read())

            # A csv_writer listát vár, megcsináljuk neki.
            sor = [ diak[key] for key in sablonok[diak['sablon']]['fejlec'] ]

            jegy_writer.writerow (sor)

    def ki(self, uid):
        '''Diák kiírása ellenőrzésképpen

        @param uid a kiírandó diák azonosítója, lehet:
            - sorszám (int vagy str),
            - név,
            - oktatási azonosító.
        @return a kiírandó szöveg
        '''
        # egy tanulósor előállítása
        toStr = lambda i: '%-15s %4s %12s' % (i[0].capitalize(), i[1], i[2].center(10))

        if type(uid) == int: # sorszám
            n = uid
            diak = self.bizOsztaly[self.nevsorById[n][1]]
        elif ' ' in uid: # név - ebben biztos van szóköz
            n = self.nevsor.index(uid)
            diak = self.bizOsztaly[self.nevsorById[n][1]]
        elif len(uid) == 11: # uid, oktatási azonosító
            diak = self.bizOsztaly[uid]
        else: # sorszám string
            n = int(uid)
            diak = self.bizOsztaly[self.nevsorById[n][1]]

        out = [diak['nev'], diak['tsz']]
        for jegy in diak['biz']:
            out.append(toStr(jegy))
        return '\n'.join(out)

class Diak():
    def __init__(self, d, head, sablon, config, maxDicseret):

        # a "Bizonyítvány export" táblázatban ezek az oszlopok vannak elöl
        diak_head = ['uid', 'nev', 'tsz', 'szulhely', 'szulido', 'mnev', 'pnev', 'om', 'hely', 'tovabb']

        # targy_azonositok: ['targy1_oraszam', 'targy0_oraszam', ...] => [0, 1,...]
        targy_azonositok = sorted([int(t.replace('targy', '').replace('_oraszam', '')) for t in head if t.endswith('_oraszam')])

        diak = {k: v for k, v in d.items() if k in diak_head}
        diak['sablon'] = sablon['sablonnev']
        diak['khely'] = diak['hely']

        diak.update(config)
        # a születési időt hosszú alakúra írjuk át
        diak['szulido'] = self.getDatum(d['szulido']) + '.'

        # üres bizonyítvány
        E, nyelv, szabad = self.newBiz(sablon)

        # ide gyűjtjük a bukásokat
        Dicseret = d['dicseret'].split('+')
        if not Dicseret[0]:
            del(Dicseret[0])

        # Ha valami extra tantárgyas dolog van, az ide jöhet:
        # Ha van extra tantárgy módosítási igény, azt az "config['pluginTantargy']" fájlba tesszük
#                if 'pluginTantargy' in self.configAll:
#                    exec(open(os.path.join(BASE, 'plugin', self.configAll['pluginTantargy'])).read())

        # egy tárgyhoz 3 mező tartozik: tárgynév, jegy, óraszám
        for t in ['targy'+str(i) for i in targy_azonositok]:
            targy, oraszam, jegy = d[t+'_nev'], d[t+'_oraszam'], d[t+'_jegy']
            if targy == '': continue
            targy = sablon['targyValodiNev'][targy]
            try:
                hely = sablon['targyHely'][targy]
            except:
                print('Nincs ilyen tárgy a listában: %s (%s %s)' % (targy, diak['nev'], diak['osztaly']))

            if hely == 'f': # szabad helyre kerülő tárgy (pl. fakultáció)
                E[szabad.pop(0)] = [targy.capitalize(), oraszam, jegy]

            elif hely == 'n': # ez egy nyelvi tárgy
                targy = targy.split()[0]
                Targy = targy.capitalize()

                # Az osztályzóvizsgás nyelvi tárgyak szerepelhetnek a rendes bizonyítványban
                # óraszámmal együtt. Ha van már ilyen tárgy, azt írjuk felül óraszám nélkül.
                E_targyak = [[i, bejegyzes] for i, bejegyzes in enumerate(E) if Targy == bejegyzes[0]]
                if E_targyak:
                    # Az eddig feldolgozott tárgyak közt találtunk egy ilyen nevűt
                    i, bejegyzes = E_targyak[0]
                    E[i] = [Targy, '---', jegy]

                else:
                    try:
                        E[nyelv.pop(0)] = [Targy, oraszam, jegy]
                    except IndexError: # Elfogyott a nyelvi hely, mehet a rendes faktoshoz
                        try:
                            E[szabad.pop(0)] = [Targy, oraszam, jegy]
                        except IndexError: # Elfogyott az összes hely
                            print('Elfogyott az összes hely:', diak)

            else:
                hely = int(hely)
                E[hely][1], E[hely][2] = oraszam, jegy

        # Ha külön van az irodalom és nyelvtan:
        if E[2][1] != '---': # Ha a nyelvtan óraszám nem üres
            E[1][0] = '--------'
            E[2][0] = 'Magyar nyelv'

        # A sor vége mindig: ... magatartás, szorgalom, igazolt, igazolatlan
        E[int(sablon['targyHely']['magatartás'])][2] = d['magatartás']
        E[int(sablon['targyHely']['szorgalom'])][2]  = d['szorgalom']
        E[int(sablon['targyHely']['igazolatlan'])][1]  = d['igazolatlan']
        try:
            E[int(sablon['targyHely']['osszes'])][1]  = '%d' % (int(d['igazolt']) + int(d['igazolatlan']))
        except:
            print('HIBA: az igazolt vagy az igazolatlan hiányzik:', d['igazolt'], d['igazolatlan'])

        # A diák adatait feltöltjük a feldolgozott bizonyítvány-értékekkel
        for i in range(1, len(E)):
            t, o, j = E[i]
            # Ha van jegye de nincs óraszáma (osztályozó vizsga), akkor az óraszám is legyen kihúzva!
            if j and not o:
                o = '---'
            diak.update({'t%02d'%i: t, 'o%02d'%i: o, 'j%02d'%i: j})

        # Hozzáadjuk a továbbhaladást és a záradékot
        jegyzet = (self.getDicseret(Dicseret, maxDicseret) + '+' + d['jegyzet']).strip('+')
        diak['jegyzet'] = '<br /><br />'.join(jegyzet.strip('+').split('+'))

        self.adatok = diak

    def newBiz(self, sablon):
        '''Egy diák bizonyítványátak sablonja, majd ezt fogjuk töltögetni az aktuális jegyekkel

        @param sablon milyen bizonyítvány-sablont használjon?

        @return <tt>[['', '---', '-------------' ], ...], [5, 6], [24, 25]</tt>
            - E: az üres bizonyítvány
            - [5, 6]: a nyelveknek fölhasználható helyek
            - [24, 25]: szabad, tetszőleges tárgynak fölhasználható helyek
        '''
        # az összes sor sémája, ez lesz feltöltve a jegyekkel
        E = [ ['', '---', '-------------' ] for i in range(sablon.nRows) ]
        E[0] = ['','','']                                         # csak a helyes számozás végett, a végén törölhető
        E[-4][1], E[-3][1], E[-2][2], E[-1][2] = ['']*4           # mag-szorg-nál nem kell évi óraszám, hiányzásnál jegy

        nyelv  = sablon['nyelv'][:]
        szabad = sablon['szabad'][:]

        # Az első szabad hely le van foglalva a hittannak - ha a szabad helyekre van beírva
        # egyébként van rendes helye (hit- és erkölcstan)
        if sablon['targyHely']['hittan'] in szabad:
            E[szabad.pop(0)][0] = 'Hittan'

        return E, nyelv, szabad

    def getDicseret(self, Dicseret, maxDicseret):
        '''generálja a dicséretes jegyzetet'''

        if   len(Dicseret) == 0:
            jegyzet = ''
        elif len(Dicseret) <= 1:
            jegyzet = 'Dicséretben részesült %s tantárgyból.' % Dicseret[0]
        elif len(Dicseret) <= maxDicseret:
            jegyzet = 'Dicséretben részesült %s és %s tantárgyakból.' % (', '.join(Dicseret[:-1]), Dicseret[-1])
        else:
            jegyzet = 'Kiváló tanulmányi munkájáért általános dicséretben részesült.'

        return jegyzet

    def getDatum(self, datum):
        '''"2007.03.08" => "2007. március 8"
        
        @param datum a dátum "2007.03.08" vagy "2007-03-08" formában
        '''
        import datetime
        ev, ho, nap = list(map(int, re.compile("[-\. ]+").split(datum)[:3]))
        d = datetime.date(ev, ho, nap).strftime("%Y. %B ") + '%s' % nap # azért így, hogy ne legyen bevezető '0' ill. ' '
        return d

if __name__ == "__main__":
    main()

