# -*- coding: utf-8  -*-
"""Unit tests for database.py."""

import unittest

import mock

import database


class TestConvertDatabaseRecord(unittest.TestCase):
    def test_convert_database_record(self):
        record = ("20140523121626", "False", "Bob", "20130523235032")
        result = database.convert_database_record(record)
        expected = (20140523121626, True, "Bob", 20130523235032)
        self.assertEqual(result, expected)


class TestGetDataForCategory(unittest.TestCase):
    """The split-query Python join is the new, bug-prone core; pin it down."""

    def setUp(self):
        self.linksdb = mock.Mock()
        self.commonsdb = mock.Mock()
        patchers = [
            mock.patch.object(database, "linksdb", self.linksdb, create=True),
            mock.patch.object(database, "commonsdb", self.commonsdb, create=True),
        ]
        for p in patchers:
            p.start()
            self.addCleanup(p.stop)

    def test_join_and_usage_membership(self):
        # Driver returns bytes; the join must still match against the in-use
        # flag from the merged links query (page_title, in_use).
        self.linksdb.query.return_value = [
            (b"A.jpg", 1),
            (b"B.jpg", 0),
            (b"C.jpg", 1),
        ]
        self.commonsdb.query.return_value = [
            (b"A.jpg", "20140523121626", b"Alice", "20130101000000"),
            (b"B.jpg", "20140524121626", b"Bob", "20140101000000"),
            (b"C.jpg", "20140525121626", b"Carol", "20140201000000"),
        ]

        result = database.get_data_for_category("Some_category")

        # A and C are in use; B is not.
        self.assertEqual(
            result,
            (
                (20140523121626, True, b"Alice", 20130101000000),
                (20140524121626, False, b"Bob", 20140101000000),
                (20140525121626, True, b"Carol", 20140201000000),
            ),
        )
        # A single links query now returns both titles and usage.
        self.assertEqual(self.linksdb.query.call_count, 1)

    def test_empty_category_short_circuits(self):
        self.linksdb.query.return_value = []
        result = database.get_data_for_category("Empty_category")
        self.assertEqual(result, ())
        # No usage or metadata queries when there are no titles.
        self.assertEqual(self.linksdb.query.call_count, 1)
        self.commonsdb.query.assert_not_called()


class TestGetDataMixin(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch("database.get_data_for_category", autospec=True)
        self.mock_get_data_for_category = patcher.start()
        self.mock_get_data_for_category.return_value = (
            (20140523121626, False, "Bob", 20130523235032),
            (20140523121626, False, "Alice", 20140528235032),
            (20140529121626, False, "Alice", 20140528235032),
            (20140530121626, False, "Alice", 20140528235032),
        )
        self.addCleanup(patcher.stop)

        self.expected_timestamp_data = {
            "20140523": {"images": 2, "joiners": 2, "newbie_joiners": 1},
            "20140529": {"images": 1, "joiners": 0, "newbie_joiners": 0},
            "20140530": {"images": 1, "joiners": 0, "newbie_joiners": 0},
        }

        self.images_count = 4
        self.usercount = 2
        self.userreg = 1
        self.usage = 0

        self.user_data = {
            "Alice": {"count": 3, "reg": 20140528235032, "usage": 0},
            "Bob": {"count": 1, "reg": 20130523235032, "usage": 0},
        }


class TestGetData(TestGetDataMixin):
    def test_GetData(self):
        competition_config = {
            "Brazil": {"start": 20140501030000, "end": 20140601025959},
        }

        result = database.getData("Dumplings2014", competition_config)

        expected = {
            "Brazil": {
                "count": self.images_count,
                "usercount": self.usercount,
                "start": 20140501030000,
                "userreg": self.userreg,
                "data": self.expected_timestamp_data,
                "users": self.user_data,
                "usage": self.usage,
                "category": "Images_from_Wiki_Loves_Dumplings_2014_in_Brazil",
                "end": 20140601025959,
            }
        }
        self.assertEqual(result, expected)


class TestGetCountryData(TestGetDataMixin):
    def test_get_country_data(self):
        category = "Images_from_Wiki_Loves_Dumplings_2014_in_Brazil"
        result = database.get_country_data(category, 20140501030000, 20140601025959)

        expected = {
            "count": self.images_count,
            "usercount": self.usercount,
            "start": 20140501030000,
            "userreg": self.userreg,
            "data": self.expected_timestamp_data,
            "users": self.user_data,
            "usage": self.usage,
            "category": category,
            "end": 20140601025959,
        }
        self.mock_get_data_for_category.assert_called_once_with(category)
        self.assertEqual(result, expected)


class TestUpdateEventData(TestGetDataMixin):
    def setUp(self):
        super(self.__class__, self).setUp()
        patcher = mock.patch("database.write_database_as_json", autospec=True)
        self.mock_write_database_as_json = patcher.start()
        self.addCleanup(patcher.stop)

    def test_udpate_event_data(self):
        self.maxDiff = None
        event_name = "dumplings2014"
        event_configuration = {
            "Azerbaijan": {
                "start": 20140430200000,
                "end": 20140531195959,
            },
            "Guinea-Bissau": {
                "start": 20140430200000,
                "end": 20140531195959,
            },
        }
        db = {}
        result = database.update_event_data(event_name, event_configuration, db)

        expected_base = {
            "count": self.images_count,
            "usercount": self.usercount,
            "start": 20140430200000,
            "userreg": self.userreg,
            "data": self.expected_timestamp_data,
            "users": self.user_data,
            "usage": self.usage,
            "end": 20140531195959,
        }

        expected_az = expected_base.copy()
        expected_az.update(
            {
                "category": "Images_from_Wiki_Loves_Dumplings_2014_in_Azerbaijan",
            }
        )
        expected_gb = expected_base.copy()
        expected_gb.update(
            {
                "category": "Images_from_Wiki_Loves_Dumplings_2014_in_Guinea-Bissau",
            }
        )

        expected = {
            "dumplings2014": {
                "Azerbaijan": expected_az,
                "Guinea-Bissau": expected_gb,
            }
        }
        self.assertEqual(result, expected)
        self.mock_write_database_as_json.assert_called_once_with(expected)


if __name__ == "__main__":
    unittest.main()
