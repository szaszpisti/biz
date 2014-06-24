#!/usr/bin/python
# coding: utf-8

import sys, os.path

BASE = os.path.dirname(__file__)
sys.path.append(BASE)

class Biz:
    global BASE
    def __init__(self, oszt, uid, bal, gerinc, fent, diff, frame):

        '''
        # Alapértelmezett oldalbeállítások:
        bal = 7        # bal margó (mindennel együtt)
        gerinc = 12    # a két tükör közötti távolság
        fent = 5       # bal oldal fölső margója
        diff = 0       # a jobb oldal mennyivel van fentebb mint a bal
        '''

        import jegy
        from yaml import load
        self.data = jegy.Bizonyitvany(oszt).bizOsztaly[uid]
        self.data.update(load(open(os.path.join(BASE, 'biz.ini'))))

        self.data.update({'bal': bal, 'gerinc': gerinc, 'fent': fent, 'diff': diff, 'frame': frame })

        self.data['tukor'] = 93     # a tükör szélessége

        # A törzslap mezőinek koordinátái a tantargyak.ini-ben vannak.
        self.torzslap = load(open(os.path.join(BASE, 'tantargyak.ini')))['sablonok'][self.data['sablon']]['torzslap']

    def drawFrame(self, c):
        from reportlab.lib.units import mm
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

#        self.fontSize1, self.fontSize2, self.fontSize3, self.fontSizeJegyzet = 9, 14, 16, 11

    def initPDF(self, pdf=None):

        data = self.data
        if data['frame'] == 'on': data['frame'] = True

        if pdf is None:
            from tempfile import mkstemp
            NULL, pdf = mkstemp('.pdf', 'biz-')
        self.filename = pdf

        ###########################################################################################

        from reportlab.pdfgen import canvas
        from reportlab.lib.enums import TA_JUSTIFY
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        self.setFontSize(10)
        self.fontBase = "DejaVu" # "Vera" # "Helvetica"

        # "DejaVu Sans Semi-Condensed" "DejaVu Sans Bold Semi-Condensed"

        # A használt betűtípusok betöltése
        pdfmetrics.registerFont(TTFont('LinBiolinum', os.path.join(BASE, 'font', 'LinBiolinum_R.ttf')))
        pdfmetrics.registerFont(TTFont('LinBiolinum-SC', os.path.join(BASE, 'font', 'LinBiolinum_aS.ttf')))
        pdfmetrics.registerFont(TTFont('LinBiolinum-Bold', os.path.join(BASE, 'font', 'LinBiolinum_RB.ttf')))
        pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSansCondensed.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', 'DejaVuSansCondensed-Bold.ttf'))

        c = canvas.Canvas(pdf, bottomup=0)
        return c

    def savePDF(self, c):
        c.save()

    def genPDF(self, fileName=None):
        c = self.initPDF(fileName)
        self.drawPDF(c)
        self.savePDF(c)

    def drawPara(self, c, posX, posY, width, text, fontName, fontSize):
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph
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

##############################################################################################

class Biz1(Biz):
    def __init__(self, oszt, uid, bal=7, gerinc=12, fent=5, diff=0, frame=False):
        Biz.__init__(self, oszt, uid, bal, gerinc, fent, diff, frame)

    def drawPDF(self, c):

        data = self.data
        if data['frame'] == 'on': data['frame'] = True

        from reportlab.lib.units import mm

        ##############################################################################################
        # JOBB OLDAL

        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # jobb oldal eltolása
        c.translate((data['bal']+data['tukor']+data['gerinc']+data['posX'])*mm, (data['fent']-data['diff']+data['posY'])*mm)

        if data['frame']: self.drawFrame(c)

        c.setFont('LinBiolinum-SC', self.fSize['Large'])
        c.drawCentredString(47*mm, (69)*mm, data['nev'])

        c.showPage()

##############################################################################################
# Törzslap
class Biz2(Biz):
    def __init__(self, oszt, uid, bal=7, gerinc=12, fent=5, diff=0, frame=False, megj1='', megj2=''):
        Biz.__init__(self, oszt, uid, bal, gerinc, fent, diff, frame)

#        self.data.update({'megj1': megj1, 'megj2': megj2})

    def drawPDF(self, c):

        data = self.data
        torzs = self.torzslap

        if data['frame'] == 'on': data['frame'] = True

        from reportlab.lib.units import mm

        ##############################################################################################
        # JOBB OLDAL

        self.fontBase = 'LinBiolinum' # "DejaVu" # "Vera" # "Helvetica"

        # jobb oldal eltolása
        c.translate((data['bal']+data['tukor']+data['gerinc']+data['posX'])*mm, (data['fent']-data['diff']+data['posY'])*mm)

        if data['frame']: self.drawFrame(c)

        c.setFont('LinBiolinum-SC', self.fSize['Large'])
        c.drawString(torzs['nev'][0]*mm, torzs['nev'][1]*mm, data['nev'])

        c.setFont(self.fontBase, self.fSize['large'])
        for key in ['uid', 'szulhely', 'szulido', 'pnev', 'mnev']:
            c.drawString(torzs[key][0]*mm, torzs[key][1]*mm, data[key])

        c.setFont(self.fontBase, self.fSize['normal'])

        c.setFont(self.fontBase, self.fSize['large'])
        for key in ['hely', 'kev', 'kho', 'knap']:
            c.drawCentredString(torzs[key][0]*mm, torzs[key][1]*mm, data[key])

        c.showPage()

##############################################################################################

class Biz3(Biz):
    def __init__(self, oszt, uid, bal=7, gerinc=12, fent=5, diff=0, frame=False):
        Biz.__init__(self, oszt, uid, bal, gerinc, fent, diff, frame)

    def targySor(self, c, y, i, diff=0):
        # diff: a jobb oldali táblázatban szélesebb a tárgy mező!
        from reportlab.lib.units import mm
        s = '%02d' % i
        d = int(i in [4, 5, 6])/2.0 # A nyelveket a vonal miatt kicsit följebb kell rakni
        c.drawString(3*mm, (y-d)*mm, self.data['t'+s])
        c.drawRightString((52+diff)*mm, y*mm, self.data['o'+s])
        c.drawCentredString((73+diff)*mm, y*mm, self.data['j'+s])

    def drawPDF(self, c):

        data = self.data
        if data['t01'][-3:] == '---': data['t01'] = '           ----------'
        if data['frame'] == 'on': data['frame'] = True

        from reportlab.lib.units import mm

        ##############################################################################################
        # BAL OLDAL
        c.saveState()

        # bal oldal eltolása
        c.translate((data['bal']+data['posX'])*mm, (data['fent']+data['posY'])*mm)

        if data['frame']: self.drawFrame(c)

        self.fontBase = 'LinBiolinum'
        c.setFont(self.fontBase, self.fSize['large'])
        c.drawCentredString(54*mm, 5*mm, data['om']) # "029752")
        c.drawCentredString(80*mm, 5*mm, data['tsz'])
        c.drawCentredString(17.5*mm, 45.1*mm, data['tanev'])

        c.setFont(self.fontBase, self.fSize['Large'])
        c.drawString(3*mm, 17*mm, data['nev'])
        c.drawRightString(65*mm, 37*mm, data['osztaly'])

        self.fontBase = 'DejaVu'
        c.setFont(self.fontBase, self.fSize['small'])

        c.setFont('DejaVu', 9)
        for i in range(1, 21):
            self.targySor(c, 51.5+i*5, i)

        c.restoreState()

        ##############################################################################################
        # JOBB OLDAL
        c.saveState()

        # jobb oldal eltolása
        c.translate((data['bal']+data['tukor']+data['gerinc']+data['posX'])*mm, (data['fent']-data['diff']+data['posY'])*mm)

        if data['frame']: self.drawFrame(c)

        c.setFont('DejaVu', 9)
        t = [8.0, 13.0, 18.0, 23.0, 29.0, 34.0, 39.0, 44.0, 49.5] # a bejegyzések helye a jobb oldalon (nem egyenletes!)
        for i in range(9):
            self.targySor(c, t[i]+1.5, i+21, 2)

        c.setFont(self.fontBase, self.fSize['normal'])

        datumY = 75.5
        c.setFont(self.fontBase, self.fSize['large'])
        c.drawRightString(46 *mm, datumY*mm, data['hely'] + '   ' + str(data['ev'])+'.')
        c.drawCentredString(64 *mm, datumY*mm, data['ho'])
        c.drawRightString(88 *mm, datumY*mm, data['nap'])

        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph
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

    oszt, uid = '7a', '72818368589'

    t = Biz1(oszt, uid, frame=True)
    t.genPDF('1.pdf')
    print t.filename

    t = Biz2(oszt, uid, frame=True)
    t.genPDF('2.pdf')
    print t.filename

    t = Biz3(oszt, uid, frame=True)
    t.genPDF('3.pdf')
    print t.filename

