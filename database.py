#!/usr/bin/python
# -*- coding: utf-8 -*-

import io
import json
import shutil
import time

from commons_database import DB, TITLE_CHUNK_SIZE, as_text, chunked
from configuration import getConfig
from functions import get_wikiloves_category_name

DATABASE_NAME = "db.json"

updateLog = []

# Query for the links (x4) cluster: resolve a category to the titles of the
# files it contains, together with whether each file is in use anywhere
# (globalimagelinks). ``categorylinks``/``linktarget``/``globalimagelinks``
# live on the links cluster; ``page`` exists on both. A correlated EXISTS
# avoids the fan-out (one globalimagelinks row per usage per wiki) that a JOIN
# would produce, matching the old `IN (SELECT DISTINCT gil_to ...)` semantics.
category_query = """SELECT page_title,
   EXISTS (SELECT 1 FROM globalimagelinks WHERE gil_to = page_title) AS in_use
 FROM categorylinks
 INNER JOIN page ON cl_from = page_id
 WHERE cl_type = 'file'
   AND cl_target_id = (SELECT lt_id FROM linktarget WHERE lt_title = %s AND lt_namespace = 14)
"""

# Query for the core (s4) cluster: image/actor/user metadata for the given file
# titles. First-uploader is resolved via the oldest oldimage revision.
metadata_query = """SELECT
 img_name,
 img_timestamp,
 COALESCE(user.user_name, actor.actor_id) as name,
 COALESCE(user_registration, "20050101000000") as user_registration
 FROM image
 LEFT JOIN oldimage ON image.img_name = oldimage.oi_name AND oldimage.oi_timestamp = (SELECT MIN(o.oi_timestamp) FROM oldimage o WHERE o.oi_name = image.img_name)
 LEFT JOIN actor ON actor.actor_id = COALESCE(oldimage.oi_actor, image.img_actor)
 LEFT JOIN user ON user.user_id = actor.actor_user
 WHERE img_name IN ({titles})
"""


def getData(name, data):
    """
    Coleta dados do banco de dados e processa
    """

    default_starttime = min(data[c]["start"] for c in data if "start" in data[c])
    default_endtime = max(data[c]["end"] for c in data if "end" in data[c])
    result_data = {}

    for country_name, country_config in data.items():
        event = name[0:-4].title()
        year = name[-4:]
        cat = get_wikiloves_category_name(event, year, country_name)
        if name == "monuments2010":
            cat = "Images_from_Wiki_Loves_Monuments_2010"

        start_time = country_config.get("start", default_starttime)
        end_time = country_config.get("end", default_endtime)
        country_data = get_country_data(cat, start_time, end_time)
        if country_data:
            result_data[country_name] = country_data
        else:
            updateLog.append(
                "%s in %s is configured, but no file was found in [[Category:%s]]"
                % (name, country_name, cat.replace("_", " "))
            )
    return result_data


def get_country_data(category, start_time, end_time):
    country_data = {}

    dbData = get_data_for_category(category)

    if not dbData:
        return None

    daily_data = (
        {}
    )  # data: {timestamp_day0: {'images': n, 'joiners': n}, timestamp_day1: ...}
    user_data = {}  # users: {'user1': {'count': n, 'usage': n, 'reg': timestamp},...}

    discarded_counter = 0

    for timestamp, usage, user, user_reg in dbData:
        user = str(user.decode())
        # Desconsidera timestamps fora do período da campanha
        if not start_time <= timestamp <= end_time:
            discarded_counter += 1
            continue
        # Conta imagens por dia
        day = str(timestamp)[0:8]
        if day not in daily_data:
            daily_data[day] = {"images": 0, "joiners": 0, "newbie_joiners": 0}

        daily_data[day]["images"] += 1

        if user not in user_data:
            daily_data[day]["joiners"] += 1
            if user_reg > start_time:
                daily_data[day]["newbie_joiners"] += 1
            user_data[user] = {"count": 0, "usage": 0, "reg": user_reg}

        user_data[user]["count"] += 1
        if usage:
            user_data[user]["usage"] += 1

    country_data.update({"data": daily_data, "users": user_data})
    country_data["usercount"] = len(user_data)
    country_data["count"] = sum(u["count"] for u in user_data.values())
    country_data["usage"] = sum(u["usage"] for u in user_data.values())
    country_data["userreg"] = len(
        [user for user in user_data.values() if user["reg"] > start_time]
    )
    country_data["category"] = category
    country_data["start"] = start_time
    country_data["end"] = end_time
    if discarded_counter:
        updateLog.append(
            "%s images discarded as out of bounds in [[Category:%s]]"
            % (discarded_counter, category.replace("_", " "))
        )

    return country_data


def get_data_for_category(category_name):
    """Query the database for a given category.

    The links tables live on the x4 cluster and can no longer be JOINed
    against the core tables, so the lookup is split across two connections and
    joined in code.

    Return: Tuple of tuples (<timestamp>, <in use>, <User>, <registration>)
    (20140529121626, False, u'Example', 20140528235032)
    """
    # Step 1 (links cluster): resolve the category to file titles, each with
    # its in-use flag (globalimagelinks) in the same query.
    category_rows = linksdb.query(category_query, (category_name,))
    if not category_rows:
        return ()
    titles = [as_text(title) for title, _ in category_rows]
    in_use = {as_text(title) for title, used in category_rows if used}

    # Step 2 (core cluster): image/actor/user metadata for those titles,
    # chunked so large categories stay under the statement-size limit. Titles
    # are normalized to str so the membership test below is type-safe.
    metadata = []
    for batch in chunked(titles, TITLE_CHUNK_SIZE):
        placeholders = ", ".join(["%s"] * len(batch))
        metadata_sql = metadata_query.format(titles=placeholders)
        metadata += commonsdb.query(metadata_sql, tuple(batch))

    # Join in code: usage is membership of img_name in the in-use set.
    return tuple(
        convert_database_record(
            (timestamp, as_text(img_name) in in_use, user, user_reg)
        )
        for (img_name, timestamp, user, user_reg) in metadata
    )


def convert_database_record(record):
    (timestamp, usage, user, user_reg) = record
    return (int(timestamp), bool(usage), user, int(user_reg or 0))


def write_database_as_json(db):
    temporary_database_name = f"{DATABASE_NAME}.new"
    with open(temporary_database_name, "w") as f:
        json.dump(db, f)
    shutil.copy(temporary_database_name, DATABASE_NAME)


def update_event_data(event_slug, event_configuration, db):
    start = time.time()
    event_data = getData(event_slug, event_configuration)
    db[event_slug] = event_data
    write_database_as_json(db)
    log = "Saved %s: %dsec, %d countries, %d uploads" % (
        event_slug,
        time.time() - start,
        len(event_data),
        sum(event_data[c].get("count", 0) for c in event_data),
    )
    print(log)
    updateLog.append(log)
    return db


if __name__ == "__main__":
    from argparse import ArgumentParser

    description = "Update the database"
    parser = ArgumentParser(description=description)
    parser.add_argument(
        "events", nargs="*", metavar="EVENTS", help="A list of events to update"
    )
    args = parser.parse_args()

    print("Fetching configuration...")
    config = getConfig("Module:WL_data")
    try:
        with open(DATABASE_NAME, "r") as f:
            db = json.load(f)
    except Exception as e:
        print(f"Erro ao abrir {DATABASE_NAME}:", repr(e))
        db = {}
    print("Found %s events in the configuration." % len(config))

    commonsdb = DB()
    linksdb = DB(links=True)

    with commonsdb, linksdb:
        if args.events:
            print(
                "Updating only %s event(s): %s."
                % (len(args.events), ", ".join(args.events))
            )
            for event_name in args.events:
                event_configuration = config.get(event_name)
                if event_configuration:
                    print("Fetching data for %s..." % event_name)
                    db = update_event_data(event_name, event_configuration, db)
                else:
                    print("Invalid event: %s" % event_name)
        else:
            print("Updating all %s events." % len(config))
            for event_name, event_configuration in config.items():
                print("Fetching data for %s..." % event_name)
                db = update_event_data(event_name, event_configuration, db)

    if updateLog:
        with io.open("update.log", "w", encoding="utf-8") as f:
            f.write(time.strftime("%Y%m%d%H%M%S") + "\n" + "\n".join(updateLog))
