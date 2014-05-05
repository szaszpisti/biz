#!/usr/bin/python
# -*- coding: utf-8 -*-

'''@package jegy
Feldolgozza az "Évvégi eredményeket"

Lefuttatva feldolgozza a "forras" könyvtárban található oszt.xls fájlokat,
mindegyikhez elkészíti az oszt.csv-t, ami a bizonyítvány input formátumában van.
'''
# python-yaml python-xlrd

import sys, string, locale, csv, re, os.path

BASE = os.path.dirname(__file__)
sys.path.append(BASE)

reload(sys)
sys.setdefaultencoding( "utf-8" )

import locale
locale.setlocale(locale.LC_ALL, 'hu_HU.UTF-8')

def main():
    '''Főprogram'''
#    print Bizonyitvany('7a', True).bizOsztaly['77642413171']
#    print getOsztalyLista().lista
    for oszt, osztaly, tmp, tmp in getOsztalyLista().lista:
        print oszt,
        t = Bizonyitvany(oszt, quiet=True)
#        t.csvOut()

class getOsztalyLista():
    '''A forrás könyvtárban található összes xls-t végigveszi,
    a fájlnevek alapján elkészíti belőle az osztálylistát
    '''
    def __init__(self):
        '''
                  osztályID, osztályNév, évfolyam, felső-e
        lista: [ ['10b',     '10. B',    10,       True],   ...]
        '''
        BASE = os.path.dirname(__file__)
        from yaml import load  
        config = load(open(os.path.join(BASE, 'biz.yaml'))) 

        ## az osztályok listája a következő formában:
        #           osztályID, osztályNév, évfolyam, felső-e
        # lista: [ ['10b',     '10. B',    10,       True],   ...]
        self.lista = []

        # vesszük a forrás könyvtárban található összes xls-t
        import glob
        xlsFiles = glob.glob(os.path.join(BASE, 'forras', '*.xls'))

        for xlsFile in xlsFiles:
            f = os.path.basename(xlsFile) # basename
            oszt = f[:f.rfind('.')]       # levágjuk a kiterjesztést
            self.lista.append(self.Osztaly(oszt))

        # rendezzük az osztálylistát évfolyam(2), majd név(1) alapján
        def sortOszt(x, y):
            if cmp(x[2], y[2]) == 0: return cmp(x[1], y[1])
            else: return cmp(x[2], y[2])
        self.lista.sort(cmp=sortOszt)

    def Osztaly(self, oszt):
        '''A paraméterként kapott osztálynevet dolgozza fel

        @param oszt: a feldolgozandó osztályazonosító ("10b")

        @return <tt>['10b', '10. B', 10, True]</tt>
        '''
        import re
        m = re.match(r'^(\d+)[^a-zA-Z]*([a-zA-Z]*)', oszt).groups()
        osztaly = '%s. %s' % (m[0], m[1].upper())
        evfolyam = int(m[0])

        felso = False
        if evfolyam > 8: felso = True

        return [oszt, osztaly, evfolyam, felso]

#    t = Bizonyitvany('10b')
#    print t.bizOsztaly['73946433164']
#    print t.ki('73946433164')
#    print t.nevsor
#    print t.ki('Török András')
#    print t.ki(5)
#    print '\n'.join(t.getNevsor())

class Bizonyitvany():
    def __init__(self, oszt, quiet=False):
        '''Egy osztályhoz tartozó bizonyítványok

        @param oszt osztályazonosító
        @param quiet ne kérdezze meg a bukásokat -> 3 bukásra automatikusan évismétlést ír be
        '''

        global BASE

        ## osztályazonosító
        self.oszt = oszt
        self.bizOsztaly = {}

        config = self.getConfig(os.path.join(BASE, 'biz.yaml'), oszt)

        self.xlsFile = os.path.join(BASE, 'forras', '%s.xls' % oszt)
        self.csvFile = os.path.join(BASE, 'forras', '%s.csv' % oszt)

        # Ha nincs még csv vagy régebbi az xls-nél, akkor generálni kell
        if not os.path.isfile(self.csvFile) or os.path.getmtime(self.csvFile) < os.path.getmtime(self.xlsFile):

            print u'\n   Nincs csv, elkészítem: %s' % self.csvFile

            try:
                # A taninformos xls-hez hozzá van csapva egy HTML dokumentum, ezt levágjuk
                # és visszaállítjuk az eredeti időbélyeget

                xlsStat = os.stat(self.xlsFile)
                xlsContent = open(self.xlsFile, 'rb').read()

                i = xlsContent.index('\r<!DOCTYPE')
                open(self.xlsFile, 'wb').write(xlsContent[:i])
                os.utime(self.xlsFile, (xlsStat.st_atime, xlsStat.st_mtime))
            except ValueError:
                pass

            import xlrd
            osztalyFile = xlrd.open_workbook(self.xlsFile).sheet_by_index(0)

            targySorrend = self.getTargySorrend(config['felso'])

            # az "Évvégi eredmények" táblázatban ezek az oszlopok vannak elöl - a szükségtelen mezőket később töröljük
            head = ['nev', 'uid', '', 'tsz', 'szulhely', 'szulido', '', 'mnev', 'pnev']

            for i in range (1, osztalyFile.nrows):
                sor = osztalyFile.row_values(i)

                # A végéről leszedjük az üres mezőket (pl. különböző sorhosszúság)
                while 1:
                    if sor[-1] != '': break
                    sor.pop()

                # egyelőre csak a személyes adatok lesznek benne; diak: {'nev': 'Sámli Samu', 'uid': '1234567890', ...}
                diak = dict(zip(head, sor[:9]))
                del(diak[''])

                if not 'Szorgalom' in sor:
                    print u'\n   *** %s (%s): hiányos a bizonyítványa, átugrom.' % (diak['nev'], oszt)
                    continue

                diak.update(config)
                # a születési időt hosszú alakúra írjuk át
                diak['szulido'] = self.getDatum(diak['szulido']) + '.'

                # üres bizonyítvány
                E, nyelv, szabad = self.newBiz(config['felso'])
                # ide gyűjtjük a bukásokat és a dicséreteket
                Bukott, Dicseret = [], []

                # a 9. oszloptól kezdődnek a jegyek, addig személyes adatok vannak, az már fel van dolgozva
                sor = sor[9:]
                # a végén 4 db "tárgy" 2-2, összesen 8 helyet foglal (mag-szorg, mulasztások)
                # egy tárgyhoz 3 mező tartozik: tárgynév, jegy, óraszám
                for t in range(0, len(sor)-8, 3):
                    if sor[t] == '': continue
                    targy, jegy, oraszam = sor[t].lower(), sor[t+1], sor[t+2]
                    try:
                        hely = targySorrend[targy]
                    except:
                        print 'Nincs ilyen tárgy a listában: %s (%s %s)' % (targy, diak['nev'], diak['osztaly'])

                    if hely == 'f': # szabad helyre kerülő tárgy (pl. fakultáció)
                        E[szabad.pop(0)] = [targy.capitalize(), oraszam, jegy]

                    elif hely == 'n': # ez egy nyelvi tárgy
                        targy = targy.split()[0]
                        E[nyelv.pop(0)] = [targy.capitalize(), oraszam, jegy]

                    else:
                        hely = int(hely)
                        E[hely][1], E[hely][2] = oraszam, jegy

                    # Ha külön van az irodalom és nyelvtan:
                    if E[2][1] != '---': # Ha a nyelvtan óraszám nem üres
                        E[1][0] = '--------'
                        E[2][0] = 'Magyar nyelv'
                    if jegy == 'elégtelen': Bukott.append(targy)
                    if jegy == 'kitűnő':  Dicseret.append(targy)

                # A sor vége mindig: ... magatartás, szorgalom, igazolt, igazolatlan
                E[int(targySorrend[u'magatartás'])][2] = sor[-7]
                E[int(targySorrend[u'szorgalom'])][2]  = sor[-5]
                E[int(targySorrend[u'igazolatlan'])][1]  = sor[-1]
                E[int(targySorrend[u'osszes'])][1]  = '%d' % (int(sor[-3]) + int(sor[-1]))

                # A diák adatait feltöltjük a feldolgozott bizonyítvány-értékekkel
                for i in range(1, len(E)):
                    t, o, j = E[i]
                    # a "kitűnő" értékelésű tárgyakat visszaírjuk "jeles"-re
                    if j == 'kitűnő': j = 'jeles'
                    diak['t%02d' % i] = t
                    diak['o%02d' % i] = o
                    diak['j%02d' % i] = j

                # Hozzáadjuk a továbbhaladást és a záradékot
                diak.update(self.getZaradek(config['evfolyam'], diak['nev'], Bukott, Dicseret, quiet))

                self.bizOsztaly[diak['uid']] = diak

            self.nevsor, self.nevsorById = self.makeNevsor()
            self.csvOut()

        else:
            # Már megvan a csv, lehet beolvasni.
            biz_reader = csv.reader(open(self.csvFile, "rb"), delimiter='\t', quoting=csv.QUOTE_MINIMAL)

            head = biz_reader.next()

            for sor in biz_reader:
                self.bizOsztaly[sor[0]] = dict(zip(head, sor))

            self.nevsor, self.nevsorById = self.makeNevsor()

    def getConfig(self, iniFile, oszt):
        '''Beolvassa a config fájlt (biz.yaml)

        @param iniFile az ini fájl neve (biz.yaml)
        @param oszt osztály azonosító

        @return a konfigurációs fájlból vett és a számított beállítások szótára
        '''
        from yaml import load
        self.configAll = load(open(iniFile))

        ''' "10b" => (10, "10. B") '''
        import re
        evfolyam = re.compile(r'[^0-9]').sub('', oszt) # '10b' => '10'

        osztaly = evfolyam + '. ' + oszt[len(evfolyam):].upper()
        evfolyam = int(evfolyam)
        config = { 'osztaly': osztaly, 'evfolyam': evfolyam }

        config['felso'] = True
        if evfolyam < 9: config['felso'] = False

        config['kev'], config['kho'], config['knap'] = re.compile("[\. ]*").split(self.configAll['beiratkozasDate'])
        if evfolyam >= 12:
            bizDate = self.configAll['vegzosDate']
        else:
            bizDate = self.configAll['bizDate']
        config['ev'], config['ho'], config['nap'] = re.compile("[\. ]*").split(bizDate)
        config['om'], config['hely'], config['khely'] = self.configAll['om'], self.configAll['hely'], self.configAll['hely']
        config['tanev'] = '%s  %s' % (int(config['ev'])-1,  config['ev'])

        return config

    def getDatum(self, datum):
        '''"2007.03.08" => "2007. március 8"
        
        @param datum a dátum "2007.03.08" formában
        '''
        import datetime
        ev, ho, nap = map(int, re.compile("[\. ]*").split(datum)[:3])
        d = datetime.date(ev, ho, nap).strftime("%Y. %B ") + '%s'%nap # azért így, hogy ne legyen bevezető '0' ill. ' '
        return d

    def getZaradek(self, evfolyam, nev, Bukott, Dicseret, quiet=False):
        '''Adott diákhoz generálja a záradékot

        @param evfolyam A diák évfolyama
        @param nev A diák neve
        @param Bukott <tt>['Tárgy', ...]</tt>
        @param Dicseret <tt>['Tárgy', ...]</tt>
        @param quiet ha True, akkor nem áll meg a legalább 3 tárgyból bukottaknál
        
        @return <tt>{'tovabb': a tanuló továbbhaladása, 'jegyzet': dicséret stb. }</tt>
        '''
        SZAMNEV = { 7:'hetedik', 8:'nyolcadik', 9:'kilencedik', 10:'tizedik', 11:'tizenegyedik', 12:'tizenkettedik', 13:'tizenharmadik' }
        if   len(Bukott) == 0:
            if evfolyam >= 12:  tovabb = 'Érettségi vizsgát tehet.'
            else:              tovabb = 'Tanulmányait a %s évfolyamon folytathatja.' % SZAMNEV[evfolyam+1]
        elif len(Bukott) <= 1: tovabb = 'Javítóvizsgát tehet %s tantárgyból.' % Bukott[0]
        elif len(Bukott) <= 3: tovabb = 'Javítóvizsgát tehet %s valamint %s tantárgyakból.' % (', '.join(Bukott[:-1]), Bukott[-1])
        else:                # tovabb = 'Évismétlés' ########  TODO  #######
            tovabb = "A %s évfolyam követelményeit nem teljesítette, az évfolyamot megismételheti." % SZAMNEV[evfolyam]
            uzenet = ("FIGYELEM!!!! Több tárgyból bukott: %s, a beírt szöveg: \n%s\n" % (nev, tovabb))
            if not quiet: raw_input (uzenet)

        if   len(Dicseret) == 0: jegyzet = ''
        elif len(Dicseret) <= 1: jegyzet = 'Dicséretben részesült %s tantárgyból.' % Dicseret[0]
        elif len(Dicseret) <= 3: jegyzet = 'Dicséretben részesült %s valamint %s tantárgyakból.' % (', '.join(Dicseret[:-1]), Dicseret[-1])
        else:                    jegyzet = 'Kiváló tanulmányi munkájáért általános dicséretben részesült.'

        return {'tovabb': tovabb, 'jegyzet': jegyzet}

    def newBiz(self, felso):
        '''Egy diák bizonyítványátak sablonja, majd ezt fogjuk töltögetni az aktuális jegyekkel

        @param felso felsős-e (9-12)? - ott más bizonyítvány van

        @return <tt>[['', '---', '-------------' ], ...], [5, 6], [24, 25]</tt>
            - E: az üres bizonyítvány
            - [5, 6]: a nyelveknek fölhasználható helyek
            - [24, 25]: szabad, tetszőleges tárgynak fölhasználható helyek
        '''
        E = [ ['', '---', '-------------' ] for i in range(30) ] # az összes sor sémája, ez lesz feltöltve a jegyekkel
        E[0] = ['','','']                                        # csak a helyes számozás végett, a végén törölhető
        E[26][1], E[27][1], E[28][2], E[29][2] = ['']*4          # mag-szorg-nál nem kell évi óraszám, hiányzásnál jegy
        if felso:                                                # a felsősöknek másképp néz ki a bizonyítványa
            E[21][0] = 'Hittan'
            nyelv = [5, 6]                                       # ide kerül a két nyelv
            szabad = [22, 23, 24, 25]                            # a hittanon kivuli szabad bizonyitvany-sorok
        else:
            E[17][0] = 'Hittan'
            nyelv = [4, 5]
            szabad = [24, 25]
        return E, nyelv, szabad

    def getTargySorrend(self, felso):
        '''A "tantargyak.csv"-ből beolvassa a tárgyakhoz tartozó helyeket

        @param felso felsős-e (9-12)? - az egyes tárgyakhoz másik oszlopban van a szám
            1. oszlop: alsó
            2. oszlop: felső
        @return <tt>{'irodalom': 1, 'matematika': 6, ...}</tt>
        '''
        import csv
        targy_reader = csv.reader(open(os.path.join(BASE, 'tantargyak.csv'), 'rb'), delimiter=';', quoting=csv.QUOTE_MINIMAL)
        targy_reader.next()

        targySorrend = {}
        for sor in targy_reader:
            if len(sor) < 3 or sor[0] == '': continue # ha kevés a mező vagy ';'-vel kezdődik
            # egy mezőhöz tartozhat több tárgynév is, ezeket vesszük sorra
            for targyNev in sor[2:]:
                targySorrend[targyNev.strip().decode('utf8')] = sor[int(felso)]

                # Ha van extra módosítási igény, azt az "config['pluginTantargy']" fájlba tesszük
                if self.configAll.has_key('pluginTantargy'):
                    exec open(BASE + '/plugin/' + self.configAll['pluginTantargy']).read()

        return targySorrend

    def makeNevsor(self):
        '''A bizOsztaly-ból névsort készít

        @return nevsor, nevsorById
           - nevsor: <tt>['Alma Attila', 'Baka Béla', ...]</tt>
           - nevsorById: <tt>[['Alma Attila', '123456789'], ['Baka Béla', '987654321'], ...]</tt>
        '''
        nevsorById = []
        for uid in self.bizOsztaly.keys():
            nevsorById.append ([self.bizOsztaly[uid]['nev'], uid])

        sort = lambda x, y: locale.strcoll(x[0], y[0])
        nevsorById.sort(cmp=sort)

        nevsor = [ nev[0] for nev in nevsorById ]
        return nevsor, nevsorById

    def csvOut(self):
        '''Fájlba írja a csv-t
        '''
        jegy_writer = csv.writer(open(self.csvFile, 'wb'), delimiter='\t')

        fejlec = self.getFejlec()

        jegy_writer.writerow(fejlec)

        for nev, uid in self.nevsorById:
            diak = self.bizOsztaly[uid]

            # Ha van extra módosítási igény, azt az "config['pluginDiak']" fájlba tesszük
            if self.configAll.has_key('pluginDiak'):
                exec open(os.path.join(BASE, 'plugin', self.configAll['pluginDiak'])).read()

            # A csv_writer listát vár, megcsináljuk neki.
            sor = [ diak[key] for key in fejlec ]

            jegy_writer.writerow (sor)

    def getFejlec(self):
        '''A fejléc mezők neveit generálja

        @return fejlec
            - fejlec: ['uid', 'osztaly', ... 't15', 'o15', 'j15', ... 'tovabb', 'jegyzet', ...]
        '''
        fejlec = ['uid', 'osztaly', 'nev', 'szulhely', 'szulido', 'pnev', 'mnev', 'khely', 'kev', 'kho', 'knap', 'om', 'tsz', 'tanev']
        for i in range(1, 30):
            fejlec.extend([ 't%02d' % i, 'o%02d' % i, 'j%02d' % i ])
        fejlec.extend(['tovabb', 'jegyzet', 'hely', 'ev', 'ho', 'nap'])

        return fejlec

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

if __name__ == "__main__":
    main()

