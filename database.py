#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import re
import sys
import time
from collections import defaultdict
from urllib import urlopen

import pymysql

from functions import get_wikiloves_category_name

updateLog = []


class DB:
    """
    Classe para fazer consultas ao banco de dados
    """

    def connect(self):
        self.conn = pymysql.connect(
            db='commonswiki_p',
            host='commonswiki.analytics.db.svc.eqiad.wmflabs',
            read_default_file=os.path.expanduser('~/replica.my.cnf'),
            read_timeout=30, charset='utf8', use_unicode=True)
        self.conn.ping(True)

    def _query(self, *sql):
        with self.conn.cursor() as cursor:
            cursor.execute(*sql)
            return cursor.fetchall()

    def query(self, *sql):
        """
        Tenta fazer a consulta, reconecta até 10 vezes até conseguir
        """
        loops = 0
        self.connect()
        while True:
            try:
                return self._query(*sql)
            except (AttributeError, pymysql.err.OperationalError):
                if loops < 10:
                    loops += 1
                    print 'Erro no DB, esperando %ds antes de tentar de novo' % loops
                    time.sleep(loops)
                else:
                    return self._query(*sql)
                    break
            else:
                print "Uncaught exception when running query"
                print sql
                break
        self.close_connection()

    def close_connection(self):
        self.conn.close()


def reData(txt, year):
    """
    Parser para linha da configuração
    """
    m = re.search(ur'''
        \s*wl\["(?P<event>earth|monuments|africa|public_art)"\]\[(?P<year>20\d\d)]\ ?=\ ?\{|
        \s*\["(?P<country>[-a-z]+)"\]\ =\ \{\["start"\]\ =\ (?P<start>%s\d{10}),\ \["end"\]\ =\ (?P<end>%s\d\d{10})\}
        ''' % (year, str(year)[:3]), txt, re.X)
    return m and m.groupdict()


def re_prefix(txt):
    return re.search(u'\s*\["(?P<prefix>[\w-]+)"\] = "(?P<name>[\w\- ]+)"|(?P<close>\})', txt)


def get_config_from_commons(page):
    api = urlopen('https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=revisions&titles=%s&rvprop=content' % page)
    text = json.loads(api.read())['query']['pages'].values()[0]['revisions'][0]['*']
    return text


def parse_config(text):
    data, event, prefixes = {}, None, {}
    lines = iter(text.split(u'\n'))
    for l in lines:
        m = re_prefix(l)
        if prefixes and m and m.group('close'):
            break
        elif m and m.group('prefix'):
            prefixes[m.group('prefix')] = m.group('name')

    for l in lines:
        g = reData(l, event[-4:] if event else ur'20\d\d')
        if not g:
            continue
        if g['event']:
            event = g['event'] + g['year']
            data[event] = {}
        elif g['country'] and event:
            if g['country'] not in prefixes:
                updateLog.append(u'Unknown prefix: ' + g['country'])
                continue
            data[event][prefixes[g['country']]] = {'start': int(g['start']), 'end': int(g['end'])}

    return {name: config for name, config in data.items() if config}


def getConfig(page):
    """
    Lê a configuração da página de configuração no Commons
    """
    text = get_config_from_commons(page)
    return parse_config(text)


catExceptions = {
    u'Armenia': u'Armenia_&_Nagorno-Karabakh',
    u'Netherlands': u'the_Netherlands',
    u'Czech Republic': u'the_Czech_Republic',
    u'Dutch Caribbean': u'the_Dutch_Caribbean',
    u'Philippines': u'the_Philippines',
    u'Seychelles': u'the_Seychelles',
    u'United Kingdom': u'the_United_Kingdom',
    u'United States': u'the_United_States'
}


dbquery = u'''SELECT
 img_timestamp,
 img_name IN (SELECT DISTINCT gil_to FROM globalimagelinks) AS image_in_use,
 user.user_name as name,
 COALESCE(user_registration, "20050101000000") as user_registration
 FROM (SELECT
   cl_to,
   cl_from
   FROM categorylinks
   WHERE cl_to = %s AND cl_type = 'file') cats
 INNER JOIN page ON cl_from = page_id
 INNER JOIN image ON page_title = img_name
 LEFT JOIN oldimage ON image.img_name = oldimage.oi_name AND oldimage.oi_timestamp = (SELECT MIN(o.oi_timestamp) FROM oldimage o WHERE o.oi_name = image.img_name)
 LEFT JOIN user ON user.user_id = COALESCE(oldimage.oi_user, image.img_user)
'''


def getData(name, data):
    """
    Coleta dados do banco de dados e processa
    """

    default_starttime = min(data[c]['start'] for c in data if 'start' in data[c])
    default_endtime = max(data[c]['end'] for c in data if 'end' in data[c])
    result_data = {}

    for country_name, country_config in data.iteritems():

        event = name[0:-4].title()
        year = name[-4:]
        cat = get_wikiloves_category_name(event, year, country_name)
        if name == 'monuments2010':
            cat = u'Images_from_Wiki_Loves_Monuments_2010'

        country_data = get_country_data(cat, country_config, default_starttime, default_endtime)
        if country_data:
            result_data[country_name] = country_data
        else:
            updateLog.append(u'%s in %s is configurated, but no file was found in [[Category:%s]]' %
                             (name, country_name, cat.replace(u'_', u' ')))
    return result_data


def get_country_data(category, country_config, default_starttime, default_endtime):
    country_data = {}

    dbData = get_data_for_category(category)

    if not dbData:
        return None

    cData = {'starttime': country_config.get('start', default_starttime),
             'endtime': country_config.get('end', default_endtime),
             'data': defaultdict(int),  # data: {timestamp_day0: n, timestamp_day1: n,...}
             'users': {}}  # users: {'user1': {'count': n, 'usage': n, 'reg': timestamp},...}

    for timestamp, usage, user, user_reg in dbData:
        # Desconsidera timestamps fora do período da campanha
        if not cData['starttime'] <= timestamp <= cData['endtime']:
            continue
        # Conta imagens por dia
        cData['data'][str(timestamp)[0:8]] += 1
        if user not in cData['users']:
            cData['users'][user] = {'count': 0, 'usage': 0, 'reg': user_reg}
        cData['users'][user]['count'] += 1
        if usage:
            cData['users'][user]['usage'] += 1

    country_data.update(
        {'data': cData['data'], 'users': cData['users']})
    country_data['usercount'] = len(cData['users'])
    country_data['count'] = sum(u['count'] for u in cData['users'].itervalues())
    country_data['usage'] = sum(u['usage'] for u in cData['users'].itervalues())
    country_data['userreg'] = sum(1 for u in cData['users'].itervalues() if u['reg'] > cData['starttime']) \
        if 'starttime' in cData else 0
    country_data['category'] = category
    country_data['start'] = country_config['start']
    country_data['end'] = country_config['end']

    return country_data


def get_data_for_category(category_name):
    """Query the database for a given category

    Return: Tuple of tuples (<timestamp>, <in use>, <User>, <registration>)
    (20140529121626, False, u'Example', 20140528235032)
    """
    query_data = commonsdb.query(dbquery, (category_name,))
    dbData = tuple(
        (int(timestamp),
         bool(usage),
         user.decode('utf-8'),
         int(user_reg or 0))
        for timestamp, usage, user, user_reg in query_data)
    return dbData


if __name__ == '__main__' and 'update' in sys.argv:
    config = getConfig(u'Module:WL_data')
    try:
        with open('db.json', 'r') as f:
            db = json.load(f)
    except Exception as e:
        print u'Erro ao abrir db.json:', repr(e)
        db = {}

    commonsdb = DB()
    for WL in config:
        start = time.time()
        db[WL] = getData(WL, config[WL])
        with open('db.json', 'w') as f:
            json.dump(db, f)
        log = 'Saved %s: %dsec, %d countries, %d uploads' % \
            (WL, time.time() - start, len(db[WL]), sum(db[WL][c].get('count', 0) for c in db[WL]))
        print log
        updateLog.append(log)
    commonsdb.conn.close()
    if updateLog:
        with open('update.log', 'w') as f:
            f.write(time.strftime('%Y%m%d%H%M%S') + '\n' + '\n'.join(updateLog))
