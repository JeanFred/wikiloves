# -*- coding: utf-8  -*-
import json
import os
import sys
import unittest

# Add parent directory to path to import app and other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import data_store
import functions
from app import app


class TestApi(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        current_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_file = os.path.join(current_path, "conf/db.dump.json")
        with open(data_file, "r") as f:
            data_store.db = json.load(f)

        # Initialize other data structures in data_store
        data_store.menu = functions.get_menu(data_store.db)
        data_store.events_data = functions.get_events_data(data_store.db)
        data_store.events_names = {
            slug: functions.get_event_name(slug)
            for slug in list(data_store.events_data.keys())
        }
        data_store.country_data = functions.get_country_data(data_store.db)

        # Mock loadDB to do nothing
        self.original_loadDB = data_store.loadDB
        data_store.loadDB = lambda: None

    def tearDown(self):
        data_store.loadDB = self.original_loadDB

    def test_events(self):
        response = self.app.get("/api/events")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("monuments", data)
        self.assertIn("earth", data)

    def test_event(self):
        response = self.app.get("/api/events/monuments2016")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("Panama", data)
        self.assertIn("Turkey", data)

    def test_event_not_found(self):
        response = self.app.get("/api/events/invalid")
        self.assertEqual(response.status_code, 404)

    def test_country(self):
        response = self.app.get("/api/country/Panama")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("monuments", data)

    def test_country_not_found(self):
        response = self.app.get("/api/country/InvalidCountry")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
