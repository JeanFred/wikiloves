# -*- coding: utf-8  -*-
"""Unit tests for functions.py."""

import json
import os
import unittest

import functions


class TestGetWikilovesCategoryName(unittest.TestCase):

    def test_get_wikiloves_category_name(self):
        result = functions.get_wikiloves_category_name("Earth", "2016", "France")
        expected = u'Images_from_Wiki_Loves_Earth_2016_in_France'
        self.assertEqual(result, expected)

    def test_get_wikiloves_category_name_using_exception(self):
        result = functions.get_wikiloves_category_name("Earth", "2016", "Netherlands")
        expected = u'Images_from_Wiki_Loves_Earth_2016_in_the_Netherlands'
        self.assertEqual(result, expected)

    def test_get_wikiloves_category_name_using_special_exception(self):
        result = functions.get_wikiloves_category_name("Monuments", "2017", "Austria")
        expected = u'Media_from_WikiDaheim_2017_in_Austria/Cultural_heritage_monuments'
        self.assertEqual(result, expected)

    def test_get_wikiloves_category_name_using_event_exception(self):
        result = functions.get_wikiloves_category_name("Science", "2017", "Estonia")
        expected = u'Images_from_Wiki_Science_Competition_2017_in_Estonia'
        self.assertEqual(result, expected)

    def test_get_wikiloves_category_name_using_edition_exception(self):
        result = functions.get_wikiloves_category_name("Science", "2015", "Estonia")
        expected = u'Images_from_European_Science_Photo_Competition_2015_in_Estonia'
        self.assertEqual(result, expected)


class TestGetEventName(unittest.TestCase):

    def test_get_event_name_wikiloves(self):
        data = {
            'earth': 'Wiki Loves Earth',
            'africa': 'Wiki Loves Africa',
            'monuments': 'Wiki Loves Monuments',
            'monuments': 'Wiki Loves Monuments',
        }
        for (event_slug, event_name) in data.items():
            result = functions.get_event_name(event_slug)
            self.assertEqual(result, event_name)

    def test_get_event_name_wikiloves_several_words(self):
        result = functions.get_event_name('public_art')
        expected = 'Wiki Loves Public Art'
        self.assertEqual(result, expected)

    def test_get_event_name_wikiloves_exception(self):
        result = functions.get_event_name('science')
        expected = 'Wiki Science Competition'
        self.assertEqual(result, expected)


class TestGetEditionName(unittest.TestCase):

    def test_get_edition_name_classic(self):
        result = functions.get_edition_name('monuments', 2016)
        expected = 'Wiki Loves Monuments 2016'
        self.assertEqual(result, expected)

    def test_get_edition_name_several_words(self):
        result = functions.get_edition_name('public_art', 2016)
        expected = 'Wiki Loves Public Art 2016'
        self.assertEqual(result, expected)

    def test_get_edition_name_exception(self):
        result = functions.get_edition_name('science', 2015)
        expected = 'European_Science_Photo_Competition_2015'
        self.assertEqual(result, expected)


class TestNormalizeCountryName(unittest.TestCase):

    def test_normalize_country_name_one_word(self):
        result = functions.normalize_country_name('Albania')
        expected = 'Albania'
        self.assertEqual(result, expected)

    def test_normalize_country_name_two_words_with_underscores(self):
        result = functions.normalize_country_name('United_States')
        expected = 'United States'
        self.assertEqual(result, expected)

    def test_normalize_country_name_two_words_with_spaces(self):
        result = functions.normalize_country_name('United States')
        expected = 'United States'
        self.assertEqual(result, expected)

    def test_normalize_country_name_three_words_with_underscores(self):
        result = functions.normalize_country_name('United_Arab_Emirates')
        expected = 'United Arab Emirates'
        self.assertEqual(result, expected)

    def test_normalize_country_name_three_words_with_spaces(self):
        result = functions.normalize_country_name('United Arab Emirates')
        expected = 'United Arab Emirates'
        self.assertEqual(result, expected)


class TestGetCountrySummary(unittest.TestCase):

    def test_get_country_summary(self):
        country_data = {
            "Turkey": {
                "earth": {
                    "2015": {
                        "count": 5,
                        "usage": 0,
                        "userreg": 0,
                        "usercount": 1
                    }
                },
                "monuments": {
                    "2016": {
                        "count": 5,
                        "usage": 0,
                        "userreg": 0,
                        "usercount": 1
                    },
                    "2017": {
                        "count": 8,
                        "usage": 0,
                        "userreg": 0,
                        "usercount": 1
                    }
                }
            },
            "Panama": {
                "earth": {
                    "2016": {
                        "count": 26,
                        "usage": 0,
                        "userreg": 2,
                        "usercount": 2
                    }
                },
                "monuments": {
                    "2016": {
                        "count": 22,
                        "usage": 0,
                        "userreg": 2,
                        "usercount": 2
                    }
                }
            },
            "Benin": {
                "africa": {
                    "2014": {
                        "count": 5,
                        "usage": 0,
                        "userreg": 0,
                        "usercount": 1
                    }
                }
            }
        }
        result = functions.get_country_summary(country_data)
        expected = {
            'Benin': [None, None, ['2014'], None, None, None, None],
            'Panama': [['2016'], ['2016'], None, None, None, None, None],
            'Turkey': [['2015'], ['2016', '2017'], None, None, None, None, None]
        }
        self.assertEqual(result, expected)


class TestProcessDataMixin(unittest.TestCase):

    def setUp(self):
        current_path = os.path.abspath(os.path.curdir)
        data_file = os.path.join(current_path, 'conf/db.dump.json')
        self.data = json.load(open(data_file, 'r'))


class TestProcessData(TestProcessDataMixin):

    def test_get_country_data(self):
        result = functions.get_country_data(self.data)
        expected = {
            u'Austria': {
                u'public_art': {
                    u'2013': {
                        'count': 5,
                        'usage': 0,
                        'usercount': 1,
                        'userreg': 0
                    }
                }
            },
            u'Benin': {
                u'africa': {
                    u'2014': {
                        'count': 5,
                        'usage': 0,
                        'usercount': 1,
                        'userreg': 0
                    }
                }
            },
            u'Estonia': {
                u'science': {
                    u'2017': {
                        'count': 9,
                        'usage': 0,
                        'usercount': 1,
                        'userreg': 0
                    }
                }
            },
            u'India': {
                u'food': {
                    u'2017': {
                        'count': 9,
                        'usage': 0,
                        'usercount': 1,
                        'userreg': 0
                    }
                },
                u'folklore': {
                    u'2022': {
                        'count': 9,
                        'usage': 0,
                        'usercount': 1,
                        'userreg': 0
                    }
                }
            },
            u'Panama': {
                u'earth': {
                    u'2015': {
                        'count': 26,
                        'usage': 0,
                        'usercount': 2,
                        'userreg': 2
                    }
                },
                u'monuments': {
                    u'2016': {
                        'count': 26,
                        'usage': 0,
                        'usercount': 2,
                        'userreg': 2
                    }
                }
            },
            u'Turkey': {
                u'earth': {
                    u'2015': {
                        'count': 5,
                        'usage': 0,
                        'usercount': 1,
                        'userreg': 0
                    }
                },
                u'monuments': {
                    u'2016': {
                        'count': 5,
                        'usage': 0,
                        'usercount': 1,
                        'userreg': 0
                    }
                }
            }
        }
        self.assertEqual(result, expected)

    def test_get_events_data(self):
        result = functions.get_events_data(self.data)
        expected = {
            u'africa': {
                u'2014': {
                    'count': 5,
                    'country_count': 1,
                    'usage': 0,
                    'usercount': 1,
                    'userreg': 0
                }
            },
            u'earth': {
                u'2015': {
                    'count': 31,
                    'country_count': 2,
                    'usage': 0,
                    'usercount': 3,
                    'userreg': 2
                }
            },
            u'food': {
                u'2017': {
                    'count': 9,
                    'country_count': 1,
                    'usage': 0,
                    'usercount': 1,
                    'userreg': 0
                }
            },
            u'folklore': {
                u'2022': {
                    'count': 9,
                    'country_count': 1,
                    'usage': 0,
                    'usercount': 1,
                    'userreg': 0
                }
            },
            u'monuments': {
                u'2016': {
                    'count': 31,
                    'country_count': 2,
                    'usage': 0,
                    'usercount': 3,
                    'userreg': 2
                }
            },
            u'public_art': {
                u'2013': {
                    'count': 5,
                    'country_count': 1,
                    'usage': 0,
                    'usercount': 1,
                    'userreg': 0
                }
            },
            u'science': {
                u'2017': {
                    'count': 9,
                    'country_count': 1,
                    'usage': 0,
                    'usercount': 1,
                    'userreg': 0
                }
            }
        }
        self.assertEqual(result, expected)

    def test_get_menu(self):
        result = functions.get_menu(self.data)
        expected = {
            u'earth': [u'2015'],
            u'monuments': [u'2016'],
            u'africa': [u'2014'],
            u'public_art': [u'2013'],
            u'science': [u'2017'],
            u'food': [u'2017'],
            u'folklore': [u'2022']
        }
        self.assertEqual(result, expected)

    def test_get_edition_data(self):
        result = functions.get_edition_data(self.data, 'monuments2016')
        expected = {
            u'Turkey': {
                u'count': 5,
                u'category': u'Images_from_Wiki_Loves_Monuments_2016_in_Turkey',
                u'end': 20160930205959,
                u'start': 20160831210000,
                u'userreg': 0,
                u'usage': 0,
                u'data': {
                    u'20160903': {
                        "images": 5,
                        "joiners": 1,
                        "newbie_joiners": 0,
                    }
                },
                u'usercount': 1,
            },
            u'Panama': {
                u'count': 26,
                u'category': u'Images_from_Wiki_Loves_Monuments_2016_in_Panama',
                u'end': 20161001045959,
                u'start': 20160901050000,
                u'userreg': 2,
                u'usage': 0,
                u'data': {
                    u'20160902': {
                        u'images': 4,
                        u'joiners': 1,
                        u'newbie_joiners': 1,
                    },
                    u'20160903': {
                        u'images': 22,
                        u'joiners': 1,
                        u'newbie_joiners': 1,
                    }
                },
                u'usercount': 2,
            }
        }
        self.assertEqual(result, expected)

    def test_get_instance_users_data(self):
        result = functions.get_instance_users_data(self.data, 'monuments2016', 'Panama')
        expected = [
            (u'Edwin Bermudez', {u'reg': 20160903173639, u'usage': 0, u'count': 22}),
            (u'Jonas David', {u'reg': 20160902064618, u'usage': 0, u'count': 4})
        ]
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
