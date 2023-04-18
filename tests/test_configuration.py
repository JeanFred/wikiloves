# -*- coding: utf-8  -*-
"""Unit tests for configuration.py."""

import unittest

import configuration


class TestReData(unittest.TestCase):

    def test_reData_event_line(self):
        input_data = 'wl["monuments"][2010] = {'
        result = configuration.reData(input_data, 2014)
        expected = {
            'country': None,
            'year': '2010',
            'end': None,
            'event': 'monuments',
            'start': None
        }
        self.assertEqual(result, expected)

    def test_reData_event_line_public_art(self):
        input_data = 'wl["public_art"][2012] = {'
        result = configuration.reData(input_data, 2014)
        expected = {
            'country': None,
            'year': '2012',
            'end': None,
            'event': 'public_art',
            'start': None
        }
        self.assertEqual(result, expected)

    def test_reData_country_line(self):
        input_data = '''
    ["az"] = {["start"] = 20170430200000, ["end"] = 20170531195959},
    '''
        result = configuration.reData(input_data, 2017)
        expected = {
            'country': 'az',
            'year': None,
            'end': '20170531195959',
            'event': None,
            'start': '20170430200000'
        }
        self.assertEqual(result, expected)


class TestRePrefix(unittest.TestCase):

    def test_re_prefix_match_ascii_line(self):
        self.assertIsNotNone(configuration.re_prefix('    ["az"] = "Azerbaijan",'))

    def test_re_prefix_match_ascii_line_with_space(self):
        self.assertIsNotNone(configuration.re_prefix('    ["gq"] = "Equatorial Guinea",'))

    def test_re_prefix_match_ascii_line_with_dash(self):
        self.assertIsNotNone(configuration.re_prefix('    ["gw"] = "Guinea-Bissau",'))

    def test_re_prefix_match_ascii_line_with_accents(self):
        self.assertIsNotNone(configuration.re_prefix('    ["re"] = "Réunion",'))

    def test_re_prefix_match_ascii_line_with_apostrophe(self):
        self.assertIsNotNone(configuration.re_prefix('    ["ci"] = "Côte d\'Ivoire",'))


class TestParseConfig(unittest.TestCase):

    def test_parse_config_empty(self):
        config = ''
        result = configuration.parse_config(config)
        expected = {}
        self.assertEqual(result, expected)

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
        result = configuration.parse_config(config)
        expected = {
            'monuments2017': {
                'Azerbaijan': {
                    'start': 20170430200000,
                    'end': 20170531195959,
                },
                'Guinea-Bissau': {
                    'start': 20170430200000,
                    'end': 20170531195959,
                },
            },
            'monuments2018': {
                'Azerbaijan': {
                    'start': 20180430200000,
                    'end': 20180531195959,
                },
                'Guinea-Bissau': {
                    'start': 20180430200000,
                    'end': 20180531195959,
                },
            }
        }
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
