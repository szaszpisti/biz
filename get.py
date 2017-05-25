#!/usr/bin/python
# encoding: utf-8

import os
import sys
import mechanize
import ssl
import urlparse
import urllib
import datetime
import yaml
import grp

ev = str((datetime.date.today() - datetime.timedelta(days=210)).year)

def chgrp(filepath, group):
    uid = os.stat(filepath).st_uid
    gid = grp.getgrnam(group).gr_gid
    os.chown(filepath, uid, gid)

# Ne reklamáljon a tanúsítvány miatt
ssl._create_default_https_context = ssl._create_unverified_context

def go(br, values):
    '''
    adott helyre ugrás
    '''
    url = br.geturl() # az aktuális url
    parsed_url = urlparse.urlparse(url)
    qs = urlparse.parse_qs(parsed_url[4])
    qs.update(values)
    if 'sub' in qs:
        del(qs['sub'])
    return urlparse.urlunparse(parsed_url[:4] + tuple([urllib.urlencode(qs, True)]) + parsed_url[5:])

def get_form(br, value, prop='id'):
    for form in br.forms():
        try:
            if value in form.attrs[prop]:
                break
        except KeyError:
            pass
    return form

br = mechanize.Browser()
br.set_handle_robots(False)
br.open('https://naplo.szepi.hu')

# [Login]
data = yaml.load(open('get.ini'))
br.select_form('loginablak')
br['userAccount'] = data['user']
br['userPassword'] = data['password']
r = br.submit()

# [Zárási statisztika]
br.open(br.click_link(text='Zárási statisztika'))
base_url = br.geturl()

# [szemeszterId]
br.form = get_form(br, 'szemeszterSelectTool')
control = br.form.find_control("szemeszterId", type="select")

for option in control.get_items():
    szemeszterId = option.attrs['value']
    label = option.attrs['label']
    if label == ev + ' / 2':
        break
print(label)

# [osztalyId]
control = get_form(br, 'osztalySelectTool').find_control("osztalyId", type="select")

osztalyok = {}
for option in control.get_items():
    osztalyId = option.attrs['value']
    label = option.attrs['label']
    if not osztalyId:
        continue

    oszt = label.split()[0].replace('.', '')
    osztalyok[oszt] = {'osztalyId': osztalyId, 'rovid': oszt, 'hosszu': label}

# Ha parancssorban volt argumentum, csak azt vesszük - egyébként az összes osztályt
if len(sys.argv) == 1:
    args = osztalyok.keys()
else:
    args = sys.argv[1:]

path = 'tanev/%s' % ev
os.chmod(path, 0o775)
chgrp(path, 'www-data')

for oszt in args:
    osztaly = osztalyok[oszt]
    osztalyId, rovid, hosszu = osztaly['osztalyId'], osztaly['rovid'], osztaly['hosszu']
    data = urllib.urlencode({'osztalyId': osztalyId, 'szemeszterId': szemeszterId})
    br.open(base_url, data)

    print oszt,
    sys.stdout.flush()

    br.form = get_form(br, 'f=download', 'action')
    br.submit()

    fn = 'tanev/%s/bizonyitvany-%s-%s.csv' % (ev, ev, oszt)
    open(fn, 'w').write(br.response().read())

# [kilépés]
url = go(br, {'page': ['session'], 'f': ['logout']})
br.open(url)

