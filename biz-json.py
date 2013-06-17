#!/usr/bin/python
# coding: utf-8

'''@file "biz-json.py"

A HTML lekérdezéseket kiszolgáló háttéralkalmazás.
Osztálylistát, névsorokat szolgáltat.
'''

import csv, sys, os.path, simplejson as json
from yaml import load

# A wsgi miatt kell tudnunk az aktuális könyvtár nevét
BASE = os.path.dirname(__file__)
sys.path.append(BASE)

## a konfigurációs fájlból vett adatok
config = load(open(BASE + '/biz.yaml'))

## a bizonyítvány-dátumból kigyűjtjük az aktuális évet
ev = config['bizDate'].split('.')[0]

def application(environ, start_response):

    '''A kérés típusa alapján (tip) ad vissza eredményt
    '''
    from jegy import Bizonyitvany
    from urlparse import parse_qsl
    query = dict(parse_qsl(environ['QUERY_STRING']))

    if query.has_key('tip'): tip = query['tip']
    else: tip = 'oszt'

    start_response('200 OK', [('Content-type', 'text/plain')])

    if tip == 'oszt':
        ''' beírja az elérhető bizonyítványok osztályait egy HTML SELECT-be '''

        from jegy import getOsztalyLista
        res = [ '<option value="%s">%s</option>' % (o[0], o[1]) for o in getOsztalyLista().lista ]

        # Automatikusan az első elem legyen kiválasztva
        # '<option value="12b">12. B</option>' ==> '<option value="12b" selected>12. B</option>'
        pre, sep, post = res[0].partition('>')
        res[0] = pre + ' selected>' + post

        data = json.dumps('\n'.join(['<select id="oszt" name="oszt">'] + res + ['</select>']))
        return [data]

    elif tip == 'nevsor':
        # adott osztálynévhez tartozó osztálynévsor
        oszt = query['oszt']
        from jegy import Bizonyitvany

        res = [ '<option value="%s">%s</option>\n' % (t[1], t[0]) for t in Bizonyitvany(oszt, quiet=True).nevsorById ]

        pre, sep, post = res[0].partition('>')
        res[0] = pre + ' selected>' + post

        data = json.dumps('\n'.join(res))
        return [data]

    elif tip == 'uid':
        oszt = query['oszt']
        uid = query['uid']

        res = Bizonyitvany(oszt, quiet=True).bizOsztaly[uid]

        data = json.dumps(res)
        return [data]

    elif tip == 'nyomtat':
        uid  = query['uid']
        oszt = query['oszt']
        pp   = query['pp']

        arg = ''
        for key in query:
            arg += '%s=%s ' % (key, query[key])
        log = open('/tmp/BIZ.txt', 'a')
        log.write(arg + '\n')

        if query.has_key('frame'): frame=True
        else: frame=False

        biz = 'Biz3'
        if   pp == '1': from bizonyitvany import Biz1 as Biz
        elif pp == '2': from bizonyitvany import Biz2 as Biz
        elif pp == '3': from bizonyitvany import Biz3 as Biz

        b = Biz(oszt, uid,
                 bal=int(query['bal']),
                 gerinc=int(query['gerinc']),
                 diff=int(query['diff']),
                 frame=frame,
               )
        if query.has_key('debug'):
            from tempfile import mkstemp
            NULL, filename = mkstemp('.pdf', 'biz-%s-%s-' % (oszt, uid))

            b.genPDF(filename)
        else:
            from os import unlink
            b.genPDF()
            printPDF(b.filename)
            unlink(b.filename)

        data = json.dumps ({'message': 'NYOMTATVA (<span style="color: white;">%s</span>) %s' % (b.filename, arg)})
        return [data]

def printPDF(filename):
    '''A pdf fájlt elküldi nyomtatóra

    @param filename ezt a fájlt kell elküldeni
    '''
    from subprocess import Popen, PIPE
    from os import waitpid

    p = Popen("gs -dSAFER -dBATCH -dNOPAUSE -dQUIET -sDEVICE=epsonc -r180 -sOutputFile=- %s | lpr -P TallyGenicom_5040" % filename, shell=True)
    sts = waitpid(p.pid, 0)


if __name__ == '__main__':
    print "Content-type: text/plain\n"
#    print application()

