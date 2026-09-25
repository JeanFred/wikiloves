# -*- coding: utf-8  -*-
"""Unit tests for images.py."""

import unittest

import mock

import images


class TestMakeImageQuery(unittest.TestCase):
    def test_placeholders_and_args(self):
        sql, args = images.make_image_query(["A.jpg", "B.jpg"], {}, 201)
        self.assertIn("img_name IN (%s, %s)", sql)
        self.assertEqual(args, ("A.jpg", "B.jpg"))
        self.assertIn("LIMIT 201", sql)
        self.assertNotIn("OFFSET", sql)

    def test_user_filter_appends_arg(self):
        sql, args = images.make_image_query(["A.jpg"], {"user": "Some_One"}, 201)
        self.assertIn("actor_name = %s", sql)
        # Underscores in the username are turned into spaces.
        self.assertEqual(args, ("A.jpg", "Some One"))


class TestGet(unittest.TestCase):
    """get() merges chunked results, re-sorts by pixels and pages."""

    def _row(self, name, pixels):
        # (img_name, md5, w, h, pixels, size, timestamp)
        return (name.encode(), b"ab", 100, 100, pixels, 12345, b"20210101000000")

    def _patch_db(self, titles_rows, image_rows):
        links = mock.Mock()
        links.query.return_value = titles_rows
        core = mock.Mock()
        core.query.return_value = image_rows
        cm_links = mock.MagicMock()
        cm_links.__enter__.return_value = links
        cm_core = mock.MagicMock()
        cm_core.__enter__.return_value = core

        def db_factory(links=False):
            return cm_links if links else cm_core

        return mock.patch.object(images, "DB", side_effect=db_factory)

    def test_empty_category_returns_empty_list(self):
        with self._patch_db([], []):
            result = images.get({"event": "earth", "year": "2021", "country": "France"})
        self.assertEqual(result, [])

    def test_results_sorted_by_pixels_desc(self):
        titles = [(b"A.jpg",), (b"B.jpg",)]
        image_rows = [self._row("A.jpg", 100), self._row("B.jpg", 900)]
        with self._patch_db(titles, image_rows):
            result = images.get({"event": "earth", "year": "2021", "country": "France"})
        names = [r[0] for r in result]
        self.assertEqual(names, ["B.jpg", "A.jpg"])
        # img_name is decoded to str.
        self.assertIsInstance(result[0][0], str)


if __name__ == "__main__":
    unittest.main()
