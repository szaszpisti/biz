#!/usr/bin/python3

import sys, os.path, yaml, jegy

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4

BASE = os.path.dirname(__file__)
sys.path.append(BASE)

from locale import setlocale, LC_ALL
setlocale(LC_ALL, 'hu_HU.UTF-8')

# Az alapvonal koordinátához képest ennyivel följebb, ill vízszintesen ennyi margóval írjuk ki a szöveget.
padX, padY = 2, 1

class Biz:
    global BASE
    def __init__(self, oszt, uid, bal, gerinc, diff, frame):

        '''
        Egy ember (uid) bizonyítványát készíti el.

        # Alapértelmezett oldalbeállítások:
        bal = 7        # bal margó (mindennel együtt)
        gerinc = 12    # a két tükör közötti távolság
        diff = 0       # a jobb oldal mennyivel van fentebb mint a bal
        '''
        self.data = jegy.Bizonyitvany(oszt).bizOsztaly[uid]
        self.data.update(yaml.load(open(os.path.join(BASE, 'biz.ini'))))

        self.data.update({'bal': bal, 'gerinc': gerinc, 'diff': diff, 'frame': frame })

        # A mezők koordinátái a sablonban vannak.
        self.sablon = yaml.load(open(os.path.join(BASE, 'sablon', self.data['sablon'] + '.ini')))

        self.data['tukor'] = self.sablon['tukor']

    def drawFrame(self, c):
        p = c.beginPath()
        p.moveTo(0, 100*mm)
        p.lineTo(0, 0)
        p.lineTo(self.data['tukor']*mm, 0)
        p.lineTo(self.data['tukor']*mm, 100*mm)
        c.drawPath(p)

    def setFontSize(self, base):
        # betűméretek:
        #   9.00 10.80 12.96 15.55 18.66
        #  10.00 12.00 14.40 17.28 20.73
        fontNames = ['small', 'normal', 'large', 'Large', 'LARGE']
        self.fSize = {}
        for i in range(len(fontNames)):
            self.fSize[fontNames[i]] = base*(1.2**i)

    def initPDF(self, pdf=None, download=False):

        data = self.data
        if data['frame'] == 'on': data['frame'] = True

        if pdf is None:
            from tempfile import mkstemp
            NULL, pdf = mkstemp('.pdf', 'biz-')
        self.filename = pdf

        ###########################################################################################

        self.setFontSize(10)
        self.fontBase = "DejaVu" # "Vera" # "Helvetica"

        # "DejaVu Sans Semi-Condensed" "DejaVu Sans Bold Semi-Condensed"

        # A használt betűtípusok betöltése
        pdfmetrics.registerFont(TTFont('LinBiolinum', os.path.join(BASE, 'font', 'LinBiolinum_R.ttf')))
        pdfmetrics.registerFont(TTFont('LinBiolinum-SC', os.path.join(BASE, 'font', 'LinBiolinum_aS.ttf')))
        pdfmetrics.registerFont(TTFont('LinBiolinum-Bold', os.path.join(BASE, 'font', 'LinBiolinum_RB.ttf')))
        pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSansCondensed.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', 'DejaVuSansCondensed-Bold.ttf'))

        c = canvas.Canvas(pdf, pagesize=A4, bottomup=0)
        # Egy picikét meg kell nyújtani, rosszul pozícionál
        # c.scale(1, 140/139)

        if download:
            c.saveState()
            c.scale(1, -1)
            c.translate(0, -842-6*mm)
            c.drawImage(os.path.join(BASE, 'sablon', self.sablon['P3']['hatter']), -3, 290, 595, 543, [1, 0])
            c.restoreState()

        return c

    def savePDF(self, c):
        c.save()

    def genPDF(self, fileName=None, download=False):
        c = self.initPDF(fileName, download)
        self.drawPDF(c)
        self.savePDF(c)

    def drawPara(self, c, posX, posY, width, text, fontName, fontSize):
        style = getSampleStyleSheet()["Normal"]
        style.fontSize = fontSize
        style.leading = 1.1 * fontSize
        style.fontName = fontName

        p = Paragraph(text, style)
        p.wrap(width, 0)
        # HACK: azért van itt, mert különben nem jól pozícionál. Miert???
        a = p.breakLines(width)
        p.drawOn(c, posX, posY + 2*style.fontSize)
        return len(a.lines)

    def outText(self, c, page, tid):
        '''Print text entry to canvas c'''
        x, y, width, size, align = self.sablon[page][tid]
        if align == 'C':
            draw = c.drawCentredString
            x = x + width/2
        elif align == 'R':
            draw = c.drawRightString
            x = x + width - padX
        else:
            draw = c.drawString
            x = x + padX

        if tid in ['om', 'tsz', 'nev']: y -= 1.5
        c.setFont(self.fontBase, self.fSize[size])
        draw(x*mm, (y-padY)*mm, self.data[tid])

        '''
        p = c.beginPath()
        p.moveTo(x*mm, y*mm)
        p.lineTo((x+10)*mm, y*mm)
        c.drawPath(p)
        '''

##############################################################################################

class Biz1(Biz):
    def __init__(self, oszt, uid, bal=7, gerinc=12, diff=0, frame=False):
        Biz.__init__(self, oszt, uid, bal, gerinc, diff, frame)

    def drawPDF(self, c):

        sablon = self.sablon
        data = self.data
        if data['frame'] == 'on': data['frame'] = True


        ##############################################################################################
        # JOBB OLDAL

        # jobb oldal eltolása
        c.translate((self.sablon['posX']+data['bal']+self.sablon['tukor']+data['gerinc'])*mm, (self.sablon['posY']-data['diff'])*mm)

        if data['frame']: self.drawFrame(c)

        self.fontBase = 'LinBiolinum-SC'
        self.outText(c, 'P1', 'nev')

        c.showPage()

##############################################################################################
# Törzslap
class Biz2(Biz):
    def __init__(self, oszt, uid, bal=7, gerinc=12, diff=0, frame=False, megj1='', megj2=''):
        Biz.__init__(self, oszt, uid, bal, gerinc, diff, frame)

    def drawPDF(self, c):
        data = self.data

        # jobb oldal eltolása
        c.translate((self.sablon['posX']+data['bal']+self.sablon['tukor']+data['gerinc'])*mm, (self.sablon['posY']-data['diff'])*mm)

        if data['frame'] == 'on': data['frame'] = True
        if data['frame']: self.drawFrame(c)

        self.fontBase = 'LinBiolinum-SC'
        self.outText(c, 'P2', 'nev')

        self.fontBase = 'LinBiolinum' # "DejaVu" # "Vera" # "Helvetica"
        for key in ['uid', 'szulhely', 'szulido', 'pnev', 'mnev', 'hely', 'kev', 'kho', 'knap']:
            self.outText(c, 'P2', key)

##############################################################################################

class Biz3(Biz):
    def __init__(self, oszt, uid, bal=7, gerinc=12, diff=0, frame=False):
        Biz.__init__(self, oszt, uid, bal, gerinc, diff, frame)

    def targySor(self, c, i, x, y):
        '''Az adott helyre kiír egy bizonyítvány sor adatot'''
        s = '%02d' % i
#        padY = 0
#        y = y-padY
        padX = 2.5
        c.drawString((x[0]+padX)*mm, (y-padY)*mm, self.data['t'+s])
        c.drawRightString((x[2]-padX)*mm, (y-padY)*mm, self.data['o'+s])
        c.drawCentredString((x[2]+x[3])/2*mm, (y-padY)*mm, self.data['j'+s])

        '''
        p = c.beginPath()
        p.moveTo(x[0]*mm, y*mm)
        p.lineTo((x[0]+10)*mm, y*mm)
        c.drawPath(p)
        '''

    def drawPDF(self, c):

        data = self.data
        if data['t01'][-3:] == '---': data['t01'] = '           ----------'
        if data['frame'] == 'on': data['frame'] = True


        ##############################################################################################
        # BAL OLDAL
        c.saveState()

        # bal oldal eltolása
        c.translate((self.sablon['posX']+data['bal'])*mm, (self.sablon['posY'])*mm)

        if data['frame']: self.drawFrame(c)

        self.fontBase = 'LinBiolinum'
        for key in ['om', 'tsz', 'nev', 'osztaly', 'tanev']:
            self.outText(c, 'P3', key)

        self.fontBase = 'DejaVu'

        c.setFont('DejaVu', 9)
        jegyCount = 0
        for y in self.sablon['P3']['bal']['y']:
            jegyCount += 1
            self.targySor(c, jegyCount, self.sablon['P3']['bal']['x'], y)

        c.restoreState()

        ##############################################################################################
        # JOBB OLDAL
        c.saveState()

        # jobb oldal eltolása
        c.translate((self.sablon['posX']+data['bal']+self.sablon['tukor']+data['gerinc'])*mm, (self.sablon['posY']-data['diff'])*mm)

        if data['frame']: self.drawFrame(c)

        c.setFont('DejaVu', 9)
        for y in self.sablon['P3']['jobb']['y']:
            jegyCount += 1
            self.targySor(c, jegyCount, self.sablon['P3']['jobb']['x'], y)

        c.setFont(self.fontBase, self.fSize['normal'])

        data['ev'] += '.'
        for key in ['hely', 'ev', 'ho', 'nap']:
            self.outText(c, 'P3', key)

        pad = 3 # a hosszabb szövegek jobb/bal margója

        style = getSampleStyleSheet()["Normal"]
        style.fontSize = self.fSize['small']
        style.leading = 1.1 * style.fontSize
        style.fontName = self.fontBase

        ######### továbbhaladás ########
        p = Paragraph(data['tovabb'], style)
        width = (data['tukor'] - 2*pad)*mm
        p.wrap(width, 0)
        # HACK: azért van itt, mert különben nem jól pozícionál. Miert???
        pData = p.breakLines(width)
        # Ha két soros a szöveg (pl. bukott), akkor kicsit föntebb legyen.
        p.drawOn(c, pad*mm, (63-2*len(pData.lines))*mm + 2*style.fontSize)

        style.fontSize = self.fSize['small']

        ######### jegyzet ########
        style.leading = 1.4 * style.fontSize
        style.spaceBefore = 20
        style.spaceAfter = 20
        p = Paragraph(data['jegyzet'], style)
        p.wrap(width, 0)
        # HACK: azért van itt, mert különben nem jól pozícionál. Miert???
        p.breakLines(width)
        p.drawOn(c, pad*mm, 118*mm + 2*style.fontSize)

        c.restoreState()
        c.showPage()

if __name__ == '__main__':

    oszt, uid = '11b', '74134134313'
    oszt, uid = '9c', '79009318453'

    '''
    t = Biz1(oszt, uid, frame=True)
    t.genPDF('1.pdf')
    print(t.filename)

    t = Biz2(oszt, uid, frame=True)
    t.genPDF('2.pdf')
    print(t.filename)
    #'''

    t = Biz3(oszt, uid, frame=True)
    t.genPDF('3.pdf')
    print(t.filename)

    t = Biz3('11b', '79088302529', frame=True)
    t.genPDF('3r.pdf')
    print(t.filename)

