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
    get_edition_name,
    get_event_name,
    get_events_data,
    get_instance_name,
    get_instance_users_data,
    get_menu,
    get_wikiloves_category_name,
    normalize_country_name
)

app = Flask(__name__)
app.debug = True

dbtime = None


def loadDB():
    global db, menu, events_data, events_names, country_data, dbtime
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
    events_names = {slug: get_event_name(slug) for slug in list(events_data.keys())}
    country_data = get_country_data(db)


loadDB()


@app.route('/')
def index():
    countries = get_country_summary(country_data)

    return render_template('mainpage.html', title='Wiki Loves Competitions Tools', menu=menu,
                           data=events_data, events_names=events_names, countries=countries)


@app.route('/log')
def logpage():
    try:
        with open('update.log', 'r') as f:
            log = f.read()
        timestamp = time.strftime('%H:%M, %d %B %Y', time.strptime(log[:14], '%Y%m%d%H%M%S'))
        log = re.sub(r'\[\[([^]]+)\]\]', lambda m: '<a href="https://commons.wikimedia.org/wiki/%s">%s</a>' %
                     (m.group(1).replace(' ', '_'), m.group(1)), log[15:]).split('\n')
    except IOError:
        log = timestamp = None
    return render_template('log.html', title='Update log', menu=menu, time=timestamp, log=log)


# All routes are explicit as we cannot just route /<scope>/ as it would also route eg /images/
@app.route('/monuments', defaults={'scope': 'monuments'})
@app.route('/earth', defaults={'scope': 'earth'})
@app.route('/africa', defaults={'scope': 'africa'})
@app.route('/public_art', defaults={'scope': 'public_art'})
@app.route('/science', defaults={'scope': 'science'})
@app.route('/food', defaults={'scope': 'food'})
@app.route('/folklore', defaults={'scope': 'folklore'})
def event_main(scope):
    if not db:
        return index()
    if scope in events_data:
        eventName = get_event_name(scope)
        eventData = {scope: {y: v for y, v in events_data[scope].items()}}
        eventData.update(countries={country: country_data[country][event] for country in country_data
                                    for event in country_data[country] if event == scope})
        return render_template('eventmain.html', title=eventName, menu=menu, scope=scope, data=eventData)
    else:
        return render_template('page_not_found.html', title='Event not found', menu=menu)


@app.route('/<scope>/20<year>')
def edition(scope, year):
    loadDB()
    if not db:
        return index()
    year = '20' + year
    edition_slug = scope + year
    if edition_slug in db:
        edition_name = get_edition_name(scope, year)
        edition_data = get_edition_data(db, edition_slug)
        return render_template('edition.html', title=edition_name, menu=menu,
                               data=edition_data, rickshaw=True)
    else:
        return render_template('page_not_found.html', title='Edition not found', menu=menu)


@app.route('/<scope>/20<year>/<country>/users')
def users(scope, year, country):
    if not db:
        return index()
    year = '20' + year
    country = normalize_country_name(country)
    edition_slug = scope + year
    if edition_slug in db and country in db[edition_slug]:
        instance_name = get_instance_name(scope, year, country)
        eventUsers = get_instance_users_data(db, edition_slug, country)
        return render_template('users.html', title=instance_name, menu=menu, scope=scope, year=year,
                               country=country, data=eventUsers, starttime=db[edition_slug][country]['start'])
    elif edition_slug in db:
        return render_template('page_not_found.html', title='Country not found', menu=menu)
    else:
        return render_template('page_not_found.html', title='Edition not found', menu=menu)


@app.route('/<scope>/20<year>/<country>')
def instance(scope, year, country):
    if not db:
        return index()
    year = '20' + year
    edition_slug = scope + year
    category_name = get_wikiloves_category_name(scope, year, country)
    country = normalize_country_name(country)
    if edition_slug in db and country in db[edition_slug]:
        instance_name = get_instance_name(scope, year, country)
        instance_daily_data = db[edition_slug][country]['data']
        return render_template('instance.html', title=instance_name, menu=menu, category_name=category_name,
                               daily_data=instance_daily_data, starttime=db[edition_slug][country]['start'])
    elif edition_slug in db:
        return render_template('page_not_found.html', title='Country not found', menu=menu)
    else:
        return render_template('page_not_found.html', title='Edition not found', menu=menu)


@app.route('/country/<name>')
def country(name):
    name = normalize_country_name(name)
    if name in country_data:
        return render_template('country.html', title='Wiki Loves Competitions in ' + name, menu=menu,
                               data=country_data[name], events_names=events_names, country=name)
    else:
        return render_template('page_not_found.html', title='Country not found', menu=menu)


@app.route('/images')
def images_page():
    args = dict(list(request.args.items()))
    imgs = images.get(args)
    if not imgs:
        return render_template('images_not_found.html', menu=menu, title='Images not found')
    backto = [args['event'], args['year']] + ([args['country']] if 'user' in args else [])
    title = 'Images of %s%s %s in %s' % (args['user'] + ' in ' if 'user' in args else '',
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
    return '%s-%s-%s' % (s[0:4], s[4:6], s[6:8])


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html', title='Page not found', menu=menu), 404


if __name__ == '__main__':
    if os.uname()[1].startswith('tools-webgrid'):
        from flup.server.fcgi_fork import WSGIServer
        WSGIServer(app).run()
    else:
        if os.environ.get('LOCAL_ENVIRONMENT', False):
            app.run(host='0.0.0.0')
        else:
            app.run()
