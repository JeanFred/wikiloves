#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import re
from urllib import urlopen

from functions import EVENTS


def reData(txt, year):
    """
    Parser para linha da configuração
    """
    events = '|'.join(EVENTS)
    regex = ur'''
        \s*wl\["(?P<event>%s)"\]\[(?P<year>20\d\d)]\ ?=\ ?\{|
        \s*\["(?P<country>[-a-z]+)"\]\ =\ \{\["start"\]\ =\ (?P<start>%s\d{10}),\ \["end"\]\ =\ (?P<end>%s\d\d{10})\}
        ''' % (events, year, str(year)[:3])
    m = re.search(regex, txt, re.X)
    return m and m.groupdict()


def re_prefix(txt):
    return re.search(r'\s*\["(?P<prefix>[\w-]+)"\] = "(?P<name>[\w\-\' ]+)"|(?P<close>\})', txt, re.UNICODE)


def get_config_from_commons(page):
    api = urlopen('https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=revisions&titles=%s&rvprop=content' % page)
    text = json.loads(api.read())['query']['pages'].values()[0]['revisions'][0]['*']
    return unicode(text)


def parse_config(text):
    data, event, prefixes = {}, None, {}
    lines = iter(text.split(u'\n'))
    for line in lines:
        m = re_prefix(line)
        if prefixes and m and m.group('close'):
            break
        elif m and m.group('prefix'):
            prefixes[m.group('prefix')] = m.group('name')

    for line in lines:
        g = reData(line, event[-4:] if event else ur'20\d\d')
        if not g:
            continue
        if g['event']:
            event = g['event'] + g['year']
            data[event] = {}
        elif g['country'] and event:
            if g['country'] not in prefixes:
                # updateLog.append(u'Unknown prefix: ' + g['country'])
                continue
            data[event][prefixes[g['country']]] = {'start': int(g['start']), 'end': int(g['end'])}

    return {name: config for name, config in data.items() if config}


def getConfig(page):
    """
    Lê a configuração da página de configuração no Commons
    """
    text = get_config_from_commons(page)
    return parse_config(text)
