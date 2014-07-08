#!/usr/bin/python3

'''@package jegy
Feldolgozza az "Évvégi eredményeket"

Lefuttatva feldolgozza a "forras" könyvtárban található oszt.xls fájlokat,
mindegyikhez elkészíti az oszt.csv-t, ami a bizonyítvány input formátumában van.
'''
# python-yaml python-xlrd

import sys, csv, os.path, yaml, locale, re, glob

locale.setlocale(locale.LC_ALL, 'hu_HU.UTF-8')

global BASE
BASE = os.path.dirname(__file__)
sys.path.append(BASE)

def main():
    '''Főprogram'''
#    print Bizonyitvany('9c', True).bizOsztaly['79536523141']
#    print getOsztalyLista().lista
    for oszt, osztaly, tmp, tmp, tmp in getOsztalyLista().lista:
        print(oszt, end=' ')
        t = Bizonyitvany(oszt, quiet=True)
#        t.csvOut()
    print()

class getOsztalyLista():
    '''A forrás könyvtárban található összes xls-t végigveszi,
    a fájlnevek alapján elkészíti belőle az osztálylistát, a hozzá tartozó sablonnevekkel
    '''
    def __init__(self):
        '''
                  osztályID, osztályNév, évfolyam, sablon
        lista: [ ['10b',     '10. B',    10,       'felso'],   ...]
        '''
        self.config = yaml.load(open(os.path.join(BASE, 'biz.ini'))) 

        ## az osztályok listája a következő formában:
        #           osztályID, osztályNév, évfolyam, felső-e
        # lista: [ ['10b',     '10. B',    10,       True],   ...]
        self.lista = []

        # vesszük a forrás könyvtárban található összes xls-t
        xlsFiles = glob.glob(os.path.join(BASE, 'forras', '*.xls'))

        for xlsFile in xlsFiles:
            f = os.path.basename(xlsFile) # basename
            oszt = f[:f.rfind('.')]       # levágjuk a kiterjesztést
            self.lista.append(self.Osztaly(oszt))

        # rendezzük az osztálylistát évfolyam(2), majd név(1) alapján
        self.lista.sort(key=lambda x: 10*x[2] + ord(x[3]))
#        from operator import itemgetter
#        self.lista = sorted(self.lista, key=itemgetter(2, 1))

    def Osztaly(self, oszt):
        '''A paraméterként kapott osztálynevet dolgozza fel

        @param oszt: a feldolgozandó osztályazonosító ("10b")

        @return <tt>['10b', '10. B', 10, 'B', '4oszt']</tt>
        '''
        import re
        for reOszt, sablon in self.config['tip']:
            if re.match(reOszt, oszt):
                break

        m = re.match(r'^(\d+)[^a-zA-Z]*([a-zA-Z]*)', oszt).groups()
        evfolyam = int(m[0])
        ab = m[1].upper()
        osztaly = '%d. %s' % (evfolyam, ab)

        return [oszt, osztaly, evfolyam, ab, sablon]

class Bizonyitvany():
    def __init__(self, oszt, quiet=False):
        '''Egy osztályhoz tartozó bizonyítványok

        @param oszt osztályazonosító
        @param quiet ne kérdezze meg a bukásokat -> 4 bukásra automatikusan évismétlést ír be
        '''

        global BASE
        self.BASE = BASE

        ## osztályazonosító
        self.oszt = oszt
        self.bizOsztaly = {}

        self.config = self.getConfig(oszt)
        self.sablon = yaml.load(open(os.path.join(BASE, 'sablon', self.config['sablon']+'.ini')))
        # Ennyi sor van összesen:
        self.sablon['nRows'] = len(self.sablon['P3']['bal']['y']) + len(self.sablon['P3']['jobb']['y']) + 1

        self.getTargySorrend(self.config['sablon'])

        self.xlsFile = os.path.join(BASE, 'forras', '%s.xls' % oszt)
        self.csvFile = os.path.join(BASE, 'forras', '%s.csv' % oszt)

        # Ha nincs még csv vagy régebbi az xls-nél, akkor generálni kell
        if not os.path.isfile(self.csvFile) or os.path.getmtime(self.csvFile) < os.path.getmtime(self.xlsFile):

            print('\n   Nincs csv, elkészítem: %s' % self.csvFile)

            try:
                # A taninformos xls-hez hozzá van csapva egy HTML dokumentum, ezt levágjuk
                # és visszaállítjuk az eredeti időbélyeget

                xlsStat = os.stat(self.xlsFile)
                xlsContent = open(self.xlsFile, 'rb').read()

                i = xlsContent.index(b'\r<!DOCTYPE')
                open(self.xlsFile, 'wb').write(xlsContent[:i])
                os.utime(self.xlsFile, (xlsStat.st_atime, xlsStat.st_mtime))
            except ValueError:
                pass

            import xlrd
            osztalyFile = xlrd.open_workbook(self.xlsFile).sheet_by_index(0)

            # az "Évvégi eredmények" táblázatban ezek az oszlopok vannak elöl - a szükségtelen mezőket később töröljük
            head = ['nev', 'uid', '', 'tsz', 'szulhely', 'szulido', '', 'mnev', 'pnev']

            for i in range (1, osztalyFile.nrows):
                sor = osztalyFile.row_values(i)

                # A végéről leszedjük az üres mezőket (különböző sorhosszúság)
                while 1:
                    if sor[-1] != '': break
                    sor.pop()

                # egyelőre csak a személyes adatok lesznek benne; diak: {'nev': 'Sámli Samu', 'uid': '1234567890', ...}
                diak = dict(list(zip(head, sor[:9])))
                del(diak[''])

                if diak['tsz'] == '':
                    print('Nincs törzslapszám: %s %5s %s' % (diak['uid'], self.config['osztaly'], diak['nev']))
                if not 'Szorgalom' in sor:
                    print('   *** %s (%s): hiányos a bizonyítványa, átugrom.' % (diak['nev'], oszt))
                    continue

                diak.update(self.config)
                # a születési időt hosszú alakúra írjuk át
                diak['szulido'] = self.getDatum(diak['szulido']) + '.'

                # üres bizonyítvány
                E, nyelv, szabad = self.newBiz()
                # ide gyűjtjük a bukásokat és a dicséreteket
                Bukott, Dicseret = [], []

                # a 9. oszloptól kezdődnek a jegyek, addig személyes adatok vannak, az már fel van dolgozva
                sor = sor[9:]
                # Ha valami extra tantárgyas dolog van, az ide jöhet:
                # Ha van extra tantárgy módosítási igény, azt az "config['pluginTantargy']" fájlba tesszük
                if 'pluginTantargy' in self.configAll:
                    exec(open(os.path.join(BASE, 'plugin', self.configAll['pluginTantargy'])).read())

                # a végén 4 db "tárgy" 2-2, összesen 8 helyet foglal (mag-szorg, mulasztások)
                # egy tárgyhoz 3 mező tartozik: tárgynév, jegy, óraszám
                for t in range(0, len(sor)-8, 3):
                    if sor[t] == '': continue
                    targy, jegy, oraszam = sor[t].lower(), sor[t+1], sor[t+2]
                    targy = self.targyValodiNev[targy]
                    try:
                        hely = self.targyHely[targy]
                    except:
                        print('Nincs ilyen tárgy a listában: %s (%s %s)' % (targy, diak['nev'], diak['osztaly']))

                    if hely == 'f': # szabad helyre kerülő tárgy (pl. fakultáció)
                        E[szabad.pop(0)] = [targy.capitalize(), oraszam, jegy]

                    elif hely == 'n': # ez egy nyelvi tárgy
                        try:
                            targy = targy.split()[0]
                            E[nyelv.pop(0)] = [targy.capitalize(), oraszam, jegy]
                        except IndexError: # Elfogyott a nyelvi hely, mehet a rendes faktoshoz
                            E[szabad.pop(0)] = [targy.capitalize(), oraszam, jegy]

                    else:
                        hely = int(hely)
                        E[hely][1], E[hely][2] = oraszam, jegy

                    if jegy == 'elégtelen': Bukott.append(self.targyValodiNev[targy])
                    if jegy == 'kitűnő':  Dicseret.append(self.targyValodiNev[targy])

                # Ha külön van az irodalom és nyelvtan:
                if E[2][1] != '---': # Ha a nyelvtan óraszám nem üres
                    E[1][0] = '--------'
                    E[2][0] = 'Magyar nyelv'

                # A sor vége mindig: ... magatartás, szorgalom, igazolt, igazolatlan
                E[int(self.targyHely['magatartás'])][2] = sor[-7]
                E[int(self.targyHely['szorgalom'])][2]  = sor[-5]
                E[int(self.targyHely['igazolatlan'])][1]  = sor[-1]
                E[int(self.targyHely['osszes'])][1]  = '%d' % (int(sor[-3]) + int(sor[-1]))

                # A diák adatait feltöltjük a feldolgozott bizonyítvány-értékekkel
                for i in range(1, len(E)):
                    t, o, j = E[i]
                    # a "kitűnő" értékelésű tárgyakat visszaírjuk "jeles"-re
                    if j == 'kitűnő': j = 'jeles'
                    diak.update({'t%02d'%i: t, 'o%02d'%i: o, 'j%02d'%i: j})

                # Hozzáadjuk a továbbhaladást és a záradékot
                diak.update(self.getZaradek(self.config['evfolyam'], diak['nev'], Bukott, Dicseret, quiet))

                self.bizOsztaly[diak['uid']] = diak

            self.nevsor, self.nevsorById = self.makeNevsor()
            self.csvOut()

        else:
            # Már megvan a csv, lehet beolvasni.
            biz_reader = csv.reader(open(self.csvFile), delimiter='\t', quoting=csv.QUOTE_MINIMAL, lineterminator=os.linesep)

            head = next(biz_reader)

            for sor in biz_reader:
                diak = dict(list(zip(head, sor)))
                self.bizOsztaly[diak['uid']] = diak

            self.nevsor, self.nevsorById = self.makeNevsor()

    def getConfig(self, oszt):
        '''Beolvassa a config fájlt (biz.ini)

        @param iniFile az ini fájl neve (biz.ini)
        @param oszt osztály azonosító

        @return a konfigurációs fájlból vett és a számított beállítások szótára
        '''
        from os.path import join

        self.configAll = yaml.load(open(join(self.BASE, 'biz.ini')))

        oszt, osztaly, evfolyam, ab, sablon = getOsztalyLista().Osztaly(oszt)
        config = { 'osztaly': osztaly, 'evfolyam': evfolyam, 'sablon': sablon }

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
        ev, ho, nap = list(map(int, re.compile("[\. ]*").split(datum)[:3]))
        d = datetime.date(ev, ho, nap).strftime("%Y. %B ") + '%s'%nap # azért így, hogy ne legyen bevezető '0' ill. ' '
        return d

    def getZaradek(self, evfolyam, nev, Bukott, Dicseret, quiet=False):
        '''Adott diákhoz generálja a záradékot

        @param evfolyam A diák évfolyama
        @param nev A diák neve
        @param Bukott <tt>['Tárgy', ...]</tt>
        @param Dicseret <tt>['Tárgy', ...]</tt>
        @param quiet ha True, akkor nem áll meg a legalább "maxBukott" tárgyból bukottaknál
        
        @return <tt>{'tovabb': a tanuló továbbhaladása, 'jegyzet': dicséret stb. }</tt>
        '''
        SZAMNEV = { 7:'hetedik', 8:'nyolcadik', 9:'kilencedik', 10:'tizedik', 11:'tizenegyedik', 12:'tizenkettedik', 13:'tizenharmadik' }
        if   len(Bukott) == 0:
            if evfolyam >= 12:  tovabb = 'Érettségi vizsgát tehet.'
            else:               tovabb = 'Tanulmányait a %s évfolyamon folytathatja.' % SZAMNEV[evfolyam+1]
        elif len(Bukott) <= 1:  tovabb = 'Javítóvizsgát tehet %s tantárgyból.' % Bukott[0]
        elif len(Bukott) <= self.configAll['maxBukott']:
                                tovabb = 'Javítóvizsgát tehet %s valamint %s tantárgyakból.' % (', '.join(Bukott[:-1]), Bukott[-1])
        else:  # tovabb = 'Évismétlés' ########  TODO  #######
            tovabb = "A %s évfolyam követelményeit nem teljesítette, az évfolyamot megismételheti." % SZAMNEV[evfolyam]
            uzenet = ("FIGYELEM!!!! Több tárgyból bukott: %s, a beírt szöveg: \n%s\n" % (nev, tovabb))
            if not quiet: input (uzenet)

        if   len(Dicseret) == 0: jegyzet = ''
        elif len(Dicseret) <= 1: jegyzet = 'Dicséretben részesült %s tantárgyból.' % Dicseret[0]
        elif len(Dicseret) <= self.configAll['maxDicseret']:
                                 jegyzet = 'Dicséretben részesült %s valamint %s tantárgyakból.' % (', '.join(Dicseret[:-1]), Dicseret[-1])
        else:                    jegyzet = 'Kiváló tanulmányi munkájáért általános dicséretben részesült.'

        return {'tovabb': tovabb, 'jegyzet': jegyzet}

    def newBiz(self):
        '''Egy diák bizonyítványátak sablonja, majd ezt fogjuk töltögetni az aktuális jegyekkel

        @param sablon milyen bizonyítvány-sablont használjon?

        @return <tt>[['', '---', '-------------' ], ...], [5, 6], [24, 25]</tt>
            - E: az üres bizonyítvány
            - [5, 6]: a nyelveknek fölhasználható helyek
            - [24, 25]: szabad, tetszőleges tárgynak fölhasználható helyek
        '''
        # az összes sor sémája, ez lesz feltöltve a jegyekkel
        E = [ ['', '---', '-------------' ] for i in range(self.sablon['nRows']) ]
        E[0] = ['','','']                                         # csak a helyes számozás végett, a végén törölhető
        E[-4][1], E[-3][1], E[-2][2], E[-1][2] = ['']*4           # mag-szorg-nál nem kell évi óraszám, hiányzásnál jegy

        nyelv  = self.sablon['nyelv'][:]
        szabad = self.sablon['szabad'][:]

        # Az első szabad hely le van foglalva a hittannak - ha a szabad helyekre van beírva
        # egyébként van rendes helye (hit- és erkölcstan)
        if self.targyHely['hittan'] in szabad:
            E[szabad.pop(0)][0] = 'Hittan'

        return E, nyelv, szabad

    def getTargySorrend(self, sablon):
        '''A "tantargyak.ini"-ből beolvassa a tárgyakhoz tartozó helyeket

        @return <tt>{'irodalom': 1, 'matematika': 6, ...}</tt>
                <tt>{'matek': 'matematika', ...}</tt>
        '''

        with open(os.path.join(BASE, 'tantargyak.ini')) as f:
            self.tantargyak = yaml.load(f)

        oszlop = self.tantargyak['helyek'][sablon]

        self.targyHely, self.targyValodiNev = {}, {}
        for t in self.tantargyak['targyak']:
            nevek, hely = t['nevek'], t['hely'][oszlop]
            # egy tárgyhoz tartozhat több név is, ezeket vesszük sorra
            # közülük az elsőt írjuk a bizonyítványba: targyValodiNev[targy álnév] -> tárgy valódi neve
            targyNev = nevek[0]
            self.targyHely[targyNev] = hely
            self.targyValodiNev[targyNev] = targyNev
            for targyAlnev in nevek[1:]:
                self.targyValodiNev[targyAlnev] = targyNev

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

        fejlec = self.getFejlec()

        jegy_writer.writerow(fejlec)

        for nev, uid in self.nevsorById:
            diak = self.bizOsztaly[uid]

            # Ha van extra módosítási igény, azt az "config['pluginDiak']" fájlba tesszük
            if 'pluginDiak' in self.configAll:
                exec(open(os.path.join(BASE, 'plugin', self.configAll['pluginDiak'])).read())

            # A csv_writer listát vár, megcsináljuk neki.
            sor = [ diak[key] for key in fejlec ]

            jegy_writer.writerow (sor)

    def getFejlec(self):
        '''A fejléc mezők neveit generálja

        @return fejlec
            - fejlec: ['sablon', 'uid', 'osztaly', ... 't15', 'o15', 'j15', ... 'tovabb', 'jegyzet', ...]
        '''
        fejlec = ['sablon', 'uid', 'osztaly', 'nev', 'szulhely', 'szulido', 'pnev', 'mnev', 'khely', 'kev', 'kho', 'knap', 'om', 'tsz', 'tanev']
        for i in range(1, self.sablon['nRows']):
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

