# -*- coding: utf-8  -*-
"""Unit tests for database.py."""

import unittest
from collections import defaultdict

import mock

import database


class TestReData(unittest.TestCase):

    def test_reData_event_line(self):
        input_data = 'wl["monuments"][2010] = {'
        result = database.reData(input_data, 2014)
        expected = {
            u'country': None,
            u'year': '2010',
            u'end': None,
            u'event': 'monuments',
            u'start': None
        }
        self.assertEqual(result, expected)

    def test_reData_event_line_public_art(self):
        input_data = 'wl["public_art"][2012] = {'
        result = database.reData(input_data, 2014)
        expected = {
            u'country': None,
            u'year': '2012',
            u'end': None,
            u'event': 'public_art',
            u'start': None
        }
        self.assertEqual(result, expected)

    def test_reData_country_line(self):
        input_data = '''
    ["az"] = {["start"] = 20170430200000, ["end"] = 20170531195959},
    '''
        result = database.reData(input_data, 2017)
        expected = {
            u'country': 'az',
            u'year': None,
            u'end': '20170531195959',
            u'event': None,
            u'start': '20170430200000'
        }
        self.assertEqual(result, expected)


class TestRePrefix(unittest.TestCase):

    def test_re_prefix_match_ascii_line(self):
        self.assertIsNotNone(database.re_prefix(u'    ["az"] = "Azerbaijan",'))

    def test_re_prefix_match_ascii_line_with_space(self):
        self.assertIsNotNone(database.re_prefix(u'    ["gq"] = "Equatorial Guinea",'))

    def test_re_prefix_match_ascii_line_with_dash(self):
        self.assertIsNotNone(database.re_prefix(u'    ["gw"] = "Guinea-Bissau",'))

    def test_re_prefix_match_ascii_line_with_accents(self):
        self.assertIsNotNone(database.re_prefix(u'    ["re"] = "Réunion",'))

    def test_re_prefix_match_ascii_line_with_apostrophe(self):
        self.assertIsNotNone(database.re_prefix(u'    ["ci"] = "Côte d\'Ivoire",'))


class TestGetDataMixin(unittest.TestCase):

    def setUp(self):
        patcher = mock.patch('database.get_data_for_category', autospec=True)
        self.mock_get_data_for_category = patcher.start()
        self.mock_get_data_for_category.return_value = (
            (20140523121626, False, u'Bob', 20130523235032),
            (20140523121626, False, u'Alice', 20140528235032),
            (20140529121626, False, u'Alice', 20140528235032),
            (20140530121626, False, u'Alice', 20140528235032),
        )
        self.addCleanup(patcher.stop)

        self.expected_timestamp_data = defaultdict(int)
        self.expected_timestamp_data.update({
            '20140523': 2,
            '20140529': 1,
            '20140530': 1
        })

        self.images_count = 4
        self.usercount = 2
        self.userreg = 1
        self.usage = 0

        self.user_data = {
            u'Alice': {
                'count': 3,
                'reg': 20140528235032,
                'usage': 0
            },
            u'Bob': {
                'count': 1,
                'reg': 20130523235032,
                'usage': 0
            }
        }


class TestGetData(TestGetDataMixin):

    def test_GetData(self):
        competition_config = {
            u'Brazil': {'start': 20140501030000, 'end': 20140601025959},
        }

        result = database.getData("Dumplings2014", competition_config)

        expected = {
            u'Brazil': {
                'count': self.images_count,
                'usercount': self.usercount,
                'start': 20140501030000,
                'userreg': self.userreg,
                'data': self.expected_timestamp_data,
                'users': self.user_data,
                'usage': self.usage,
                'category': u'Images_from_Wiki_Loves_Dumplings_2014_in_Brazil',
                'end': 20140601025959
            }
        }
        self.assertEquals(result, expected)


class TestGetCountryData(TestGetDataMixin):

    def test_get_country_data(self):
        category = u'Images_from_Wiki_Loves_Dumplings_2014_in_Brazil'
        result = database.get_country_data(category, 20140501030000, 20140601025959)

        expected = {
            'count': self.images_count,
            'usercount': self.usercount,
            'start': 20140501030000,
            'userreg': self.userreg,
            'data': self.expected_timestamp_data,
            'users': self.user_data,
            'usage': self.usage,
            'category': category,
            'end': 20140601025959
        }
        self.mock_get_data_for_category.assert_called_once_with(category)
        self.assertEquals(result, expected)


class TestUpdateEventData(TestGetDataMixin):

    def setUp(self):
        super(self.__class__, self).setUp()
        patcher = mock.patch('database.write_database_as_json', autospec=True)
        self.mock_write_database_as_json = patcher.start()
        self.addCleanup(patcher.stop)

    def test_udpate_event_data(self):
        self.maxDiff = None
        event_name = u'dumplings2014'
        event_configuration = {
            u'Azerbaijan': {
                'start': 20140430200000,
                'end': 20140531195959,
            },
            u'Guinea-Bissau': {
                'start': 20140430200000,
                'end': 20140531195959,
            },
        }
        db = {}
        result = database.update_event_data(event_name, event_configuration, db)

        expected_base = {
            'count': self.images_count,
            'usercount': self.usercount,
            'start': 20140430200000,
            'userreg': self.userreg,
            'data': self.expected_timestamp_data,
            'users': self.user_data,
            'usage': self.usage,
            'end': 20140531195959
        }

        expected_az = expected_base.copy()
        expected_az.update({
            'category': u'Images_from_Wiki_Loves_Dumplings_2014_in_Azerbaijan',
        })
        expected_gb = expected_base.copy()
        expected_gb.update({
            'category': u'Images_from_Wiki_Loves_Dumplings_2014_in_Guinea-Bissau',
        })

        expected = {
            u'dumplings2014': {
                u'Azerbaijan': expected_az,
                u'Guinea-Bissau': expected_gb,
            }
        }
        self.assertEquals(result, expected)
        self.mock_write_database_as_json.assert_called_once_with(expected)


class TestParseConfig(unittest.TestCase):

    def test_parse_config_empty(self):
        config = ''
        result = database.parse_config(config)
        expected = {}
        self.assertEquals(result, expected)

    def test_parse_config(self):
        config = '''
wl["prefixes"] = {
    ["az"] = "Azerbaijan",
    ["gw"] = "Guinea-Bissau"
}

wl["monuments"][2017] = {
    ["az"] = {["start"] = 20170430200000, ["end"] = 20170531195959},
    ["gw"] = {["start"] = 20170430200000, ["end"] = 20170531195959},
}

wl["monuments"][2018] = {
    ["az"] = {["start"] = 20180430200000, ["end"] = 20180531195959},
    ["gw"] = {["start"] = 20180430200000, ["end"] = 20180531195959},
}

'''
        result = database.parse_config(config)
        expected = {
            u'monuments2017': {
                u'Azerbaijan': {
                    'start': 20170430200000,
                    'end': 20170531195959,
                },
                u'Guinea-Bissau': {
                    'start': 20170430200000,
                    'end': 20170531195959,
                },
            },
            u'monuments2018': {
                u'Azerbaijan': {
                    'start': 20180430200000,
                    'end': 20180531195959,
                },
                u'Guinea-Bissau': {
                    'start': 20180430200000,
                    'end': 20180531195959,
                },
            }
        }
        self.assertEquals(result, expected)


if __name__ == "__main__":
    unittest.main()
