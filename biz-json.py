#!/usr/bin/python
# coding: utf-8

import cgi, csv, sys, simplejson as json

from yaml import load
data = load(open('biz.yaml'))

ev = data['bizDate'].split('.')[0]

query = cgi.FieldStorage()

def main():
    if query.has_key('tip'): tip = query['tip'].value
    else: tip = 'oszt'
    forras = 'forras'

    from jegy import Bizonyitvany

    if tip == 'oszt':
        ''' beírja az elérhető bizonyítványok osztályait egy HTML SELECT-be '''

        from jegy import getOsztalyLista
        res = [ '<option value="%s">%s</option>' % (o[0], o[1]) for o in getOsztalyLista().lista ]

        # Automatikusan az első elem legyen kiválasztva
        # '<option value="12b">12. B</option>' ==> '<option value="12b" selected>12. B</option>'
        pre, sep, post = res[0].partition('>')
        res[0] = pre + ' selected>' + post

        return json.dumps('\n'.join(['<select id="oszt" name="oszt">'] + res + ['</select>']))

    elif tip == 'nevsor':
        # adott osztálynévhez tartozó osztálynévsor
        oszt = query['oszt'].value
        from jegy import Bizonyitvany

        res = [ '<option value="%s">%s</option>\n' % (t[1], t[0]) for t in Bizonyitvany(oszt, quiet=True).nevsorId ]

        pre, sep, post = res[0].partition('>')
        res[0] = pre + ' selected>' + post

        return json.dumps('\n'.join(res))

    elif tip == 'uid':
        oszt = query['oszt'].value
        uid = query['uid'].value

        res = Bizonyitvany(oszt, quiet=True).bizOsztaly[uid]
        return json.dumps(res)

    elif tip == 'nyomtat':
        uid  = query['uid'].value
        oszt = query['oszt'].value
        pp   = query['pp'].value

        arg = ''
        for key in query:
            arg += '%s=%s ' % (key, query[key].value)
        log = open('/tmp/BIZ.txt', 'a')
        log.write(arg + '\n')

        if query.has_key('frame'): frame=True
        else: frame=False

        biz = 'Biz3'
        if   pp == '1': from bizonyitvany import Biz1 as Biz
        elif pp == '2': from bizonyitvany import Biz2 as Biz
        elif pp == '3': from bizonyitvany import Biz3 as Biz

        b = Biz(oszt, uid,
                 bal=int(query['bal'].value),
                 gerinc=int(query['gerinc'].value),
                 diff=int(query['diff'].value),
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

        return json.dumps ({'message': 'NYOMTATVA (<span style="color: white;">%s</span>) %s' % (b.filename, arg)})

def printPDF(filename):

    from subprocess import Popen, PIPE
    from os import waitpid

    p = Popen("gs -dSAFER -dBATCH -dNOPAUSE -dQUIET -sDEVICE=epsonc -r180 -sOutputFile=- %s | lpr -P TallyGenicom_5040" % filename, shell=True)
    sts = waitpid(p.pid, 0)


if __name__ == '__main__':
    print "Content-type: text/plain\n"
    print main()

