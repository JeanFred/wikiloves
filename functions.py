# -*- coding: utf-8  -*-


EVENTS = [
    'earth',
    'monuments',
    'africa',
    'public_art',
]


def get_country_data(db):
    country_data = {}
    for e in db:
        for c in db[e]:
            country_data.setdefault(c, {}).setdefault(e[:-4], {}).update({e[-4:]: {
                'count': db[e][c]['count'], 'usercount': db[e][c]['usercount'],
                'usage': db[e][c]['usage'], 'userreg': db[e][c]['userreg']}})
    return country_data


def get_daily_data_for_country(db):
    country_data = {}
    for edition in db:
        scope = edition[:-4]
        year = edition[-4:]
        for country in db[edition]:
            country_data.setdefault(country, {}).setdefault(scope, {}).update({
                year: db[edition][country]['data']
            })
    return country_data


def get_events_data(db):
    return {
        name: {
            e[-4:]: {
                'count': sum(db[e][c]['count'] for c in db[e]),
                'usercount': sum(db[e][c]['usercount'] for c in db[e]),
                'userreg': sum(db[e][c]['userreg'] for c in db[e]),
                'usage': sum(db[e][c]['usage'] for c in db[e]),
                'country_count': len(db[e])
            }
            for e in db if e[:-4] == name
        } for name in set(e[:-4] for e in db)
    }


def get_edition_data(db, edition_slug):
    return {
        country: {
            field: db[edition_slug][country][field]
            for field in db[edition_slug][country] if field != 'users'
        } for country in db[edition_slug]
    }


def get_instance_users_data(db, edition_slug, country):
    return sorted(
            db[edition_slug][country]['users'].items(),
            key=lambda i: (i[1]['count'], i[0]), reverse=True)


def get_menu(db):
    return {
        name: sorted(e[-4:] for e in db if e[:-4] == name)
        for name in set(e[:-4] for e in db)
       }


def get_country_summary(country_data):
    return {c: [(sorted(country_data[c][event].keys())if event in country_data[c] else None)
                for event in EVENTS]
            for c in country_data}


def get_event_name(event_slug):
    """
    Generate a name from the label.

    Returns title case with underscore replaced.
    """
    return u'Wiki Loves %s' % event_slug.replace('_', ' ').title()


def get_edition_name(scope_slug, year):
    return u'%s %s' % (get_event_name(scope_slug), year)


def get_instance_name(scope_slug, year, country):
    return u'%s %s in %s' % (get_event_name(scope_slug), year, country)


def get_wikiloves_category_name(event_slug, year, country):
    if (event_slug, year, country) in special_exceptions:
        return special_exceptions[(event_slug, year, country)]

    event = get_event_name(event_slug)
    template = get_event_category_template()
    country_name = catExceptions.get(country, country)
    return template.format(event=event, year=year, country=country_name).replace(' ', u'_')


def get_event_category_template():
    return u'Images_from_{event}_{year}_in_{country}'


catExceptions = {
    u'Armenia': u'Armenia_&_Nagorno-Karabakh',
    u'Netherlands': u'the_Netherlands',
    u'Central African Republic': u'the_Central_African_Republic',
    u'Comoros': u'the_Comoros',
    u'Czech Republic': u'the_Czech_Republic',
    u'Democratic Republic of the Congo': u'the_Democratic_Republic_of_the_Congo',
    u'Republic of the Congo': u'the_Republic_of_the_Congo',
    u'Dutch Caribbean': u'the_Dutch_Caribbean',
    u'Philippines': u'the_Philippines',
    u'Seychelles': u'the_Seychelles',
    u'United Arab Emirates': u'the_United_Arab_Emirates',
    u'United Kingdom': u'the_United_Kingdom',
    u'United States': u'the_United_States'
}

special_exceptions = {
    ("Monuments", "2018", "Austria"): 'Media_from_WikiDaheim_2018_in_Austria/Cultural_heritage_monuments',
    ("Monuments", "2017", "Austria"): 'Media_from_WikiDaheim_2017_in_Austria/Cultural_heritage_monuments',
    ("Monuments", "2013", "Armenia"): 'Images_from_Wiki_Loves_Monuments_2013_in_Armenia',
}
