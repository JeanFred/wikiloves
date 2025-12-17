# -*- coding: utf-8  -*-

from flask import Blueprint, jsonify

import data_store
from functions import normalize_country_name

api = Blueprint("api", __name__)


@api.route("/api/events")
def events():
    data_store.loadDB()
    if not data_store.events_data:
        return jsonify({"error": "Database not loaded"}), 503
    return jsonify(data_store.events_data)


@api.route("/api/events/<slug>")
def event(slug):
    data_store.loadDB()
    if not data_store.db:
        return jsonify({"error": "Database not loaded"}), 503

    if slug in data_store.db:
        return jsonify(data_store.db[slug])
    else:
        return jsonify({"error": "Event not found"}), 404


@api.route("/api/country/<name>")
def country(name):
    data_store.loadDB()
    if not data_store.country_data:
        return jsonify({"error": "Database not loaded"}), 503

    name = normalize_country_name(name)
    if name in data_store.country_data:
        return jsonify(data_store.country_data[name])
    else:
        return jsonify({"error": "Country not found"}), 404
