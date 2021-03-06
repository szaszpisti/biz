#!/usr/bin/python3

'''@file "biz-json.py"

A HTML lekérdezéseket kiszolgáló háttéralkalmazás.
Osztálylistát, névsorokat szolgáltat.
'''

import sys
import os.path
import simplejson as json
import tempfile
import yaml

# A wsgi miatt kell tudnunk az aktuális könyvtár nevét
BASE = os.path.dirname(__file__)
sys.path.append(BASE)

import local

from locale import setlocale, LC_ALL
setlocale(LC_ALL, 'hu_HU.UTF-8')

## a konfigurációs fájlból vett adatok
#config = yaml.load(open(os.path.join(BASE, 'biz.ini')))

## a bizonyítvány-dátumból kigyűjtjük az aktuális évet
#ev = config['bizDate'].split('.')[0]

def application(environ, start_response):

    '''A kérés típusa alapján (tip) ad vissza eredményt
    '''
    from jegy import Bizonyitvany
    from urllib.parse import parse_qsl
    query = dict(parse_qsl(environ['QUERY_STRING']))

    if 'tip' in query:
        tip = query['tip']
    else:
        tip = 'tanev'

    if 'tanev' in query:
        tanev = int(query['tanev'])
    else:
        tanev = local.get_last_tanev()

    start_response('200 OK', [('Content-type', 'text/plain')])

    if tip == 'sablon':
        sablon = query['sablon']
        '''Az aktuális sablonhoz tartozó adatok (méretek, stb.)'''
        res = local.Sablon(sablon)
        return [json.dumps(res).encode('utf-8')]

    elif tip == 'tanev':
        ''' beírja az elérhető tanéveket egy HTML SELECT-be '''

        res = [ '<option value="%s">%s</option>' % (t, t) for t in local.get_tanevek() ]

        # Automatikusan az utolsó tanév legyen kiválasztva
        # '<option value="2012">2012</option>' ==> '<option value="2012" selected>2012</option>'
        pre, sep, post = res[-1].partition('>')
        res[-1] = pre + ' selected>' + post

        data = '\n'.join(['<select id="selectTanev" name="tanev">'] + res + ['</select>'])
        return [data.encode('utf-8')]

    elif tip == 'oszt':
        ''' beírja az elérhető bizonyítványok osztályait egy HTML SELECT-be '''

        from jegy import getOsztalyLista
        res = [ '<option value="%s">%s</option>' % (o[0], o[1]) for o in getOsztalyLista(tanev).lista ]

        # Automatikusan az első elem legyen kiválasztva
        # '<option value="12b">12. B</option>' ==> '<option value="12b" selected>12. B</option>'
        pre, sep, post = res[0].partition('>')
        res[0] = pre + ' selected>' + post

        data = '\n'.join(['<select id="oszt" name="oszt">'] + res + ['</select>'])
        return [data.encode('utf-8')]

    elif tip == 'nevsor':
        # adott osztálynévhez tartozó osztálynévsor
        oszt = query['oszt']
        from jegy import Bizonyitvany

        res = [ '<option value="%s">%s</option>\n' % (t[1], t[0]) for t in Bizonyitvany(tanev, oszt, quiet=True).nevsorById ]

        pre, sep, post = res[0].partition('>')
        res[0] = pre + ' selected>' + post

        data = '\n'.join(res)
        return [data.encode('utf-8')]

    elif tip == 'uid':
        oszt = query['oszt']
        uid = query['uid']

        res = Bizonyitvany(tanev, oszt, quiet=True).bizOsztaly[uid]

        data = json.dumps(res)
        return [data.encode('utf-8')]

    elif tip == 'nyomtat':
        uid  = query['uid']
        oszt = query['oszt']
        pp   = query['pp']

        arg = ''
        for key in query:
            arg += '%s=%s ' % (key, query[key])
        log = open(os.path.join(tempfile.gettempdir(), 'BIZ.txt'), 'a')
        log.write(arg + '\n')

        if 'frame' in query: frame=True
        else: frame=False

        biz = 'Biz3'
        if   pp == '1': from bizonyitvany import Biz1 as Biz
        elif pp == '2': from bizonyitvany import Biz2 as Biz
        elif pp == '3': from bizonyitvany import Biz3 as Biz

        b = Biz(tanev, oszt, uid,
                 bal=int(query['bal']),
                 gerinc=int(query['gerinc']),
                 diff=float(query['diff']),
                 frame=frame,
               )

        if 'download' in query:

            from tempfile import mkstemp
            import unicodedata
            nev = unicodedata.normalize('NFKD', b.data['nev']).encode('ascii','ignore').decode('utf-8').replace(' ', '_')
            NULL, filename = mkstemp('.pdf', 'biz-%s-%s-%s-' % (oszt, nev, uid))
            b.genPDF(filename, download=True)
            file_path = filename
            size = os.path.getsize(filename)
            BLOCK_SIZE = 4096
            headers = [
                ('Content-type', 'application/pdf'),
                ("Content-length", str(size)),
                ('Content-Disposition', 'attachment; filename=' + filename.split('/')[-1])]
            start_response('200 OK', headers)
            def send_file(filename):
                with open(filename, 'rb') as f:
                    block = f.read(BLOCK_SIZE)
                    while block:
                        yield block
                        block = f.read(BLOCK_SIZE)
            return send_file(filename)

        if 'debug' in query:
            from tempfile import mkstemp
            NULL, filename = mkstemp('.pdf', 'biz-%s-%s-' % (oszt, uid))

            b.genPDF(filename)

        else:
            from os import unlink
            b.genPDF()
            printPDF(b.filename, '%s (%s) - %s' % (b.data['nev'], oszt, pp))
            unlink(b.filename)

        data = json.dumps ({'message': 'NYOMTATVA (<span style="color: white;">%s</span>) %s' % (b.filename, arg)})
        return [data.encode('utf-8')]

def printPDF(filename, nev):
    '''A pdf fájlt elküldi nyomtatóra

    @param filename ezt a fájlt kell elküldeni
    '''
    import subprocess
    subprocess.call(("gs -dSAFER -dBATCH -dNOPAUSE -dQUIET -sDEVICE=epsonc -r180 -sOutputFile=- %s | lpr -T '%s' -U szaszi -P TallyGenicom_5040" % (filename, nev)).encode('utf-8'), shell=True)

if __name__ == '__main__':

    if 'HTTP_REFERER' in os.environ:
        print("Content-type: text/plain\n")
    else:
        if(len(sys.argv) > 1):
            q = sys.argv[1]
        else:
            q = 'tip=tanev'
        print(application({'QUERY_STRING': q}, print))
#        application({'QUERY_STRING': q}, print)
