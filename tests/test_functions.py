# -*- coding: utf-8  -*-
"""Unit tests for functions.py."""

import json
import os
import unittest

import functions


class TestGetWikilovesCategoryName(unittest.TestCase):
    def test_get_wikiloves_category_name(self):
        result = functions.get_wikiloves_category_name("Earth", "2016", "France")
        expected = "Images_from_Wiki_Loves_Earth_2016_in_France"
        self.assertEqual(result, expected)

    def test_get_wikiloves_category_name_using_exception(self):
        result = functions.get_wikiloves_category_name("Earth", "2016", "Netherlands")
        expected = "Images_from_Wiki_Loves_Earth_2016_in_the_Netherlands"
        self.assertEqual(result, expected)

    def test_get_wikiloves_category_name_using_special_exception(self):
        result = functions.get_wikiloves_category_name("Monuments", "2017", "Austria")
        expected = "Media_from_WikiDaheim_2017_in_Austria/Cultural_heritage_monuments"
        self.assertEqual(result, expected)

    def test_get_wikiloves_category_name_using_event_exception(self):
        result = functions.get_wikiloves_category_name("Science", "2017", "Estonia")
        expected = "Images_from_Wiki_Science_Competition_2017_in_Estonia"
        self.assertEqual(result, expected)

    def test_get_wikiloves_category_name_using_edition_exception(self):
        result = functions.get_wikiloves_category_name("Science", "2015", "Estonia")
        expected = "Images_from_European_Science_Photo_Competition_2015_in_Estonia"
        self.assertEqual(result, expected)


class TestGetEventName(unittest.TestCase):
    def test_get_event_name_wikiloves(self):
        data = {
            "earth": "Wiki Loves Earth",
            "africa": "Wiki Loves Africa",
            "monuments": "Wiki Loves Monuments",
            "monuments": "Wiki Loves Monuments",
        }
        for (event_slug, event_name) in list(data.items()):
            result = functions.get_event_name(event_slug)
            self.assertEqual(result, event_name)

    def test_get_event_name_wikiloves_several_words(self):
        result = functions.get_event_name("public_art")
        expected = "Wiki Loves Public Art"
        self.assertEqual(result, expected)

    def test_get_event_name_wikiloves_exception(self):
        result = functions.get_event_name("science")
        expected = "Wiki Science Competition"
        self.assertEqual(result, expected)


class TestGetEditionName(unittest.TestCase):
    def test_get_edition_name_classic(self):
        result = functions.get_edition_name("monuments", 2016)
        expected = "Wiki Loves Monuments 2016"
        self.assertEqual(result, expected)

    def test_get_edition_name_several_words(self):
        result = functions.get_edition_name("public_art", 2016)
        expected = "Wiki Loves Public Art 2016"
        self.assertEqual(result, expected)

    def test_get_edition_name_exception(self):
        result = functions.get_edition_name("science", 2015)
        expected = "European_Science_Photo_Competition_2015"
        self.assertEqual(result, expected)


class TestNormalizeCountryName(unittest.TestCase):
    def test_normalize_country_name_one_word(self):
        result = functions.normalize_country_name("Albania")
        expected = "Albania"
        self.assertEqual(result, expected)

    def test_normalize_country_name_two_words_with_underscores(self):
        result = functions.normalize_country_name("United_States")
        expected = "United States"
        self.assertEqual(result, expected)

    def test_normalize_country_name_two_words_with_spaces(self):
        result = functions.normalize_country_name("United States")
        expected = "United States"
        self.assertEqual(result, expected)

    def test_normalize_country_name_three_words_with_underscores(self):
        result = functions.normalize_country_name("United_Arab_Emirates")
        expected = "United Arab Emirates"
        self.assertEqual(result, expected)

    def test_normalize_country_name_three_words_with_spaces(self):
        result = functions.normalize_country_name("United Arab Emirates")
        expected = "United Arab Emirates"
        self.assertEqual(result, expected)


class TestGetCountrySummary(unittest.TestCase):
    def test_get_country_summary(self):
        country_data = {
            "Turkey": {
                "earth": {
                    "2015": {"count": 5, "usage": 0, "userreg": 0, "usercount": 1}
                },
                "monuments": {
                    "2016": {"count": 5, "usage": 0, "userreg": 0, "usercount": 1},
                    "2017": {"count": 8, "usage": 0, "userreg": 0, "usercount": 1},
                },
            },
            "Panama": {
                "earth": {
                    "2016": {"count": 26, "usage": 0, "userreg": 2, "usercount": 2}
                },
                "monuments": {
                    "2016": {"count": 22, "usage": 0, "userreg": 2, "usercount": 2}
                },
            },
            "Benin": {
                "africa": {
                    "2014": {"count": 5, "usage": 0, "userreg": 0, "usercount": 1}
                }
            },
        }
        result = functions.get_country_summary(country_data)
        expected = {
            "Benin": [None, None, ["2014"], None, None, None, None],
            "Panama": [["2016"], ["2016"], None, None, None, None, None],
            "Turkey": [["2015"], ["2016", "2017"], None, None, None, None, None],
        }
        self.assertEqual(result, expected)


class TestProcessDataMixin(unittest.TestCase):
    def setUp(self):
        current_path = os.path.abspath(os.path.curdir)
        data_file = os.path.join(current_path, "conf/db.dump.json")
        self.data = json.load(open(data_file, "r"))


class TestProcessData(TestProcessDataMixin):
    def test_get_country_data(self):
        result = functions.get_country_data(self.data)
        expected = {
            "Austria": {
                "public_art": {
                    "2013": {"count": 5, "usage": 0, "usercount": 1, "userreg": 0}
                }
            },
            "Benin": {
                "africa": {
                    "2014": {"count": 5, "usage": 0, "usercount": 1, "userreg": 0}
                }
            },
            "Estonia": {
                "science": {
                    "2017": {"count": 9, "usage": 0, "usercount": 1, "userreg": 0}
                }
            },
            "India": {
                "food": {
                    "2017": {"count": 9, "usage": 0, "usercount": 1, "userreg": 0}
                },
                "folklore": {
                    "2022": {"count": 9, "usage": 0, "usercount": 1, "userreg": 0}
                },
            },
            "Panama": {
                "earth": {
                    "2015": {"count": 26, "usage": 0, "usercount": 2, "userreg": 2}
                },
                "monuments": {
                    "2016": {"count": 26, "usage": 0, "usercount": 2, "userreg": 2}
                },
            },
            "Turkey": {
                "earth": {
                    "2015": {"count": 5, "usage": 0, "usercount": 1, "userreg": 0}
                },
                "monuments": {
                    "2016": {"count": 5, "usage": 0, "usercount": 1, "userreg": 0}
                },
            },
        }
        self.assertEqual(result, expected)

    def test_get_events_data(self):
        result = functions.get_events_data(self.data)
        expected = {
            "africa": {
                "2014": {
                    "count": 5,
                    "country_count": 1,
                    "usage": 0,
                    "usercount": 1,
                    "userreg": 0,
                }
            },
            "earth": {
                "2015": {
                    "count": 31,
                    "country_count": 2,
                    "usage": 0,
                    "usercount": 3,
                    "userreg": 2,
                }
            },
            "food": {
                "2017": {
                    "count": 9,
                    "country_count": 1,
                    "usage": 0,
                    "usercount": 1,
                    "userreg": 0,
                }
            },
            "folklore": {
                "2022": {
                    "count": 9,
                    "country_count": 1,
                    "usage": 0,
                    "usercount": 1,
                    "userreg": 0,
                }
            },
            "monuments": {
                "2016": {
                    "count": 31,
                    "country_count": 2,
                    "usage": 0,
                    "usercount": 3,
                    "userreg": 2,
                }
            },
            "public_art": {
                "2013": {
                    "count": 5,
                    "country_count": 1,
                    "usage": 0,
                    "usercount": 1,
                    "userreg": 0,
                }
            },
            "science": {
                "2017": {
                    "count": 9,
                    "country_count": 1,
                    "usage": 0,
                    "usercount": 1,
                    "userreg": 0,
                }
            },
        }
        self.assertEqual(result, expected)

    def test_get_menu(self):
        result = functions.get_menu(self.data)
        expected = {
            "earth": ["2015"],
            "monuments": ["2016"],
            "africa": ["2014"],
            "public_art": ["2013"],
            "science": ["2017"],
            "food": ["2017"],
            "folklore": ["2022"],
        }
        self.assertEqual(result, expected)

    def test_get_edition_data(self):
        result = functions.get_edition_data(self.data, "monuments2016")
        expected = {
            "Turkey": {
                "count": 5,
                "category": "Images_from_Wiki_Loves_Monuments_2016_in_Turkey",
                "end": 20160930205959,
                "start": 20160831210000,
                "userreg": 0,
                "usage": 0,
                "data": {
                    "20160903": {
                        "images": 5,
                        "joiners": 1,
                        "newbie_joiners": 0,
                    }
                },
                "usercount": 1,
            },
            "Panama": {
                "count": 26,
                "category": "Images_from_Wiki_Loves_Monuments_2016_in_Panama",
                "end": 20161001045959,
                "start": 20160901050000,
                "userreg": 2,
                "usage": 0,
                "data": {
                    "20160902": {
                        "images": 4,
                        "joiners": 1,
                        "newbie_joiners": 1,
                    },
                    "20160903": {
                        "images": 22,
                        "joiners": 1,
                        "newbie_joiners": 1,
                    },
                },
                "usercount": 2,
            },
        }
        self.assertEqual(result, expected)

    def test_get_instance_users_data(self):
        result = functions.get_instance_users_data(self.data, "monuments2016", "Panama")
        expected = [
            ("Edwin Bermudez", {"reg": 20160903173639, "usage": 0, "count": 22}),
            ("Jonas David", {"reg": 20160902064618, "usage": 0, "count": 4}),
        ]
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
