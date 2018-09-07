#!/usr/bin/python
# -*- coding: utf-8  -*-

import json
import os
import re
import time
from os.path import getmtime

from flask import Flask, make_response, render_template, request

import images
from functions import (
    get_country_data,
    get_country_summary,
    get_edition_data,
    get_event_name,
    get_events_data,
    get_menu
)

app = Flask(__name__)
app.debug = True

dbtime = None


def loadDB():
    global db, menu, events_data, country_data, dbtime
    mtime = getmtime('db.json')
    if dbtime and dbtime == mtime:
        return
    dbtime = mtime
    try:
        with open('db.json', 'r') as f:
            db = json.load(f)
    except IOError:
        db = None
    menu = get_menu(db)
    events_data = get_events_data(db)
    country_data = get_country_data(db)


loadDB()


@app.route('/')
def index():
    countries = get_country_summary(country_data)
    return render_template('mainpage.html', title=u'Wiki Loves Competitions Tools', menu=menu,
                           data=events_data, countries=countries)


@app.route('/log')
def logpage():
    try:
        with open('update.log', 'r') as f:
            log = f.read()
        timestamp = time.strftime('%H:%M, %d %B %Y', time.strptime(log[:14], '%Y%m%d%H%M%S'))
        log = re.sub(ur'\[\[([^]]+)\]\]', lambda m: u'<a href="https://commons.wikimedia.org/wiki/%s">%s</a>' %
                     (m.group(1).replace(u' ', u'_'), m.group(1)), log[15:]).split(u'\n')
    except IOError:
        log = timestamp = None
    return render_template('log.html', title=u'Update log', menu=menu, time=timestamp, log=log)


# All routes are explicit as we cannot just route /<name>/ as it would also route eg /images/
@app.route('/monuments', defaults={'name': 'monuments'})
@app.route('/earth', defaults={'name': 'earth'})
@app.route('/africa', defaults={'name': 'africa'})
@app.route('/public_art', defaults={'name': 'public_art'})
def event_main(name):
    if not db:
        return index()
    if name in events_data:
        eventName = get_event_name(name)
        eventData = {name: {y: v for y, v in events_data[name].iteritems()}}
        eventData.update(countries={country: country_data[country][event] for country in country_data
                                    for event in country_data[country] if event == name})
        return render_template('eventmain.html', title=eventName, menu=menu, name=name, data=eventData)
    else:
        return render_template('page_not_found.html', title=u'Event not found', menu=menu)


@app.route('/<name>/20<year>')
def event_year(name, year):
    loadDB()
    if not db:
        return index()
    year = '20' + year
    event = name + year
    if event in db:
        eventName = u'%s %s' % (get_event_name(name), year)
        eventData = get_edition_data(db, event)
        return render_template('event.html', title=eventName, menu=menu, name=name, year=year,
                               data=eventData, rickshaw=True)
    else:
        return render_template('page_not_found.html', title=u'Event not found', menu=menu)


@app.route('/<name>/20<year>/<country>')
def users(name, year, country):
    if not db:
        return index()
    year = '20' + year
    event = name + year
    if event in db and country in db[event]:
        eventName = u'%s %s in %s' % (get_event_name(name), year, country)
        eventUsers = sorted(db[event][country]['users'].items(), key=lambda i: (i[1]['count'], i[0]), reverse=True)
        return render_template('users.html', title=eventName, menu=menu, name=name, year=year,
                               country=country, data=eventUsers, starttime=db[event][country]['start'])
    elif event in db:
        return render_template('page_not_found.html', title=u'Country not found', menu=menu)
    else:
        return render_template('page_not_found.html', title=u'Event not found', menu=menu)


@app.route('/country/<name>')
def country(name):
    if name in country_data:
        return render_template('country.html', title=u'Wiki Loves Competitions in ' + name, menu=menu,
                               data=country_data[name], country=name)
    else:
        return render_template('page_not_found.html', title=u'Country not found', menu=menu)


@app.route('/images')
def images_page():
    args = dict(request.args.items())
    imgs = images.get(args)
    if not imgs:
        return render_template('images_not_found.html', menu=menu, title=u'Images not found')
    backto = [args['event'], args['year']] + ([args['country']] if 'user' in args else [])
    title = u'Images of %s%s %s in %s' % (args['user'] + u' in ' if 'user' in args else u'',
                                          get_event_name(args['event']),
                                          args['year'], args['country'])
    return render_template('images.html', menu=menu, title=title, images=imgs, backto=backto)


@app.route('/db.json')
def download():
    response = make_response(json.dumps(db))
    response.headers["Content-Disposition"] = "attachment; filename=db.json"
    response.headers["Content-type"] = "application/json"
    return response


@app.template_filter(name='date')
def date_filter(s):
    if type(s) == int:
        s = str(s)
    return '%s.%s.%s' % (s[6:8], s[4:6], s[0:4])


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html', title=u'Page not found', menu=menu), 404


if __name__ == '__main__':
    if os.uname()[1].startswith('tools-webgrid'):
        from flup.server.fcgi_fork import WSGIServer
        WSGIServer(app).run()
    else:
        if os.environ.get('LOCAL_ENVIRONMENT', False):
            app.run(host='0.0.0.0')
        else:
            app.run()
