# -*- coding: utf-8  -*-


EVENTS = [
    'earth',
    'monuments',
    'africa',
    'public_art',
    'science',
    'food',
]


def get_country_data(db):
    country_data = {}
    for edition_slug in db:
        scope_slug = edition_slug[:-4]
        year = edition_slug[-4:]
        for country in db[edition_slug]:
            country_data.setdefault(country, {}).setdefault(scope_slug, {}).update({year: {
                'count': db[edition_slug][country]['count'],
                'usercount': db[edition_slug][country]['usercount'],
                'usage': db[edition_slug][country]['usage'],
                'userreg': db[edition_slug][country]['userreg']}
                }
            )
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


def normalize_country_name(country_name):
    return country_name.replace('_', ' ')


def get_event_name(event_slug):
    """
    Generate a name from the label.

    Returns title case with underscore replaced.
    """
    default = u'Wiki Loves %s' % event_slug.replace('_', ' ').title()
    return event_exceptions.get(event_slug.lower(), default)


def get_edition_name(scope_slug, year):
    default = u'%s %s' % (get_event_name(scope_slug), year)
    return edition_exceptions.get((scope_slug.lower(), str(year)), default)


def get_instance_name(scope_slug, year, country):
    return u'%s %s in %s' % (get_event_name(scope_slug), year, country)


def get_wikiloves_category_name(event_slug, year, country):
    if (event_slug, year, country) in special_exceptions:
        return special_exceptions[(event_slug, year, country)]

    edition = get_edition_name(event_slug, year)
    template = get_event_category_template()
    country_name = catExceptions.get(country, country)
    return template.format(edition=edition, country=country_name).replace(' ', u'_')


def get_event_category_template():
    return u'Images_from_{edition}_in_{country}'


event_exceptions = {
    u'science': 'Wiki Science Competition',
}

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

edition_exceptions = {
    ("science", "2015"): 'European_Science_Photo_Competition_2015',
}

special_exceptions = {
    ("Monuments", "2020", "Austria"): 'Media_from_WikiDaheim_2020_in_Austria/Cultural_heritage_monuments',
    ("Monuments", "2019", "Austria"): 'Media_from_WikiDaheim_2019_in_Austria/Cultural_heritage_monuments',
    ("Monuments", "2018", "Austria"): 'Media_from_WikiDaheim_2018_in_Austria/Cultural_heritage_monuments',
    ("Monuments", "2017", "Austria"): 'Media_from_WikiDaheim_2017_in_Austria/Cultural_heritage_monuments',
    ("Monuments", "2022", "Armenia"): 'Images_from_Wiki_Loves_Monuments_2022_in_Armenia',
    ("Monuments", "2021", "Armenia"): 'Images_from_Wiki_Loves_Monuments_2021_in_Armenia',
    ("Monuments", "2020", "Armenia"): 'Images_from_Wiki_Loves_Monuments_2020_in_Armenia',
    ("Monuments", "2019", "Armenia"): 'Images_from_Wiki_Loves_Monuments_2019_in_Armenia',
    ("Monuments", "2013", "Armenia"): 'Images_from_Wiki_Loves_Monuments_2013_in_Armenia',
    ("Earth", "2020", "Armenia"): 'Images_from_Wiki_Loves_Earth_2020_in_Armenia',
    ("Earth", "2021", "Armenia"): 'Images_from_Wiki_Loves_Earth_2021_in_Armenia',
    ("Earth", "2021", "United Arab Emirates"): 'Images_from_Wiki_Loves_Earth_2021_in_United_Arab_Emirates',
    ("Earth", "2022", "United Arab Emirates"): 'Images_from_Wiki_Loves_Earth_2021_in_United_Arab_Emirates',
    ("Science", "2015", "Armenia"): 'Images_from_European_Science_Photo_Competition_2015_in_Armenia',
    ("Science", "2013", "Estonia"): 'Images_from_Teadusfoto_2013',
    ("Science", "2012", "Estonia"): 'Images_from_Teadusfoto_2012',
    ("Science", "2011", "Estonia"): 'Images_from_Teadusfoto_2011',
}
