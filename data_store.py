# -*- coding: utf-8  -*-

import json
from os.path import getmtime

from functions import (
    get_country_data,
    get_event_name,
    get_events_data,
    get_menu,
)

db = None
menu = None
events_data = None
events_names = None
country_data = None
dbtime = None


def loadDB():
    global db, menu, events_data, events_names, country_data, dbtime
    try:
        mtime = getmtime("db.json")
    except OSError:
        mtime = None

    if dbtime and dbtime == mtime:
        return
    dbtime = mtime
    try:
        with open("db.json", "r") as f:
            db = json.load(f)
    except IOError:
        db = None

    if db:
        menu = get_menu(db)
        events_data = get_events_data(db)
        events_names = {slug: get_event_name(slug) for slug in list(events_data.keys())}
        country_data = get_country_data(db)
    else:
        menu = {}
        events_data = {}
        events_names = {}
        country_data = {}
