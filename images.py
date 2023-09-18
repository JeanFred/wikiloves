# -*- coding: utf-8  -*-

from commons_database import DB
from functions import get_wikiloves_category_name, normalize_country_name


def makeQuery(args):
    if "event" in args and "year" in args and "country" in args:
        country = normalize_country_name(args["country"])
        category = get_wikiloves_category_name(
            args["event"].title(), args["year"], country
        )
        queryArgs = (category,)
    else:
        return
    start = (
        "start" in args and args.get("start").isdigit() and int(args.get("start")) or 0
    )
    params = {}
    params["user"] = " AND img_user_text = %s" if "user" in args else ""
    if params["user"]:
        queryArgs += (args["user"].replace("_", " "),)
    params["start"] = " OFFSET " + str(args.get("start")) if start else ""
    params["mb"] = minmax(
        args.get("minmb"),
        args.get("maxmb"),
        " AND img_size",
        lambda n: int(n) * 1048576,
    )
    params["mp"] = minmax(
        args.get("minmp"),
        args.get("maxmp"),
        " HAVING pixels",
        lambda n: int(n) * 1000000,
    )
    params["timestamp"] = minmax(
        args.get("from"),
        args.get("until"),
        " AND img_timestamp",
        lambda n: len(n) == 14 and n,
    )
    return (
        """SELECT
 img_name,
 SUBSTR(MD5(img_name), 1, 2),
 img_width,
 img_height,
 (img_width * img_height) pixels,
 img_size,
 img_timestamp
 FROM categorylinks
 INNER JOIN page ON cl_from = page_id
 INNER JOIN image ON page_title = img_name
 WHERE cl_to = %s AND cl_type = 'file' AND img_major_mime = 'image'{user}{timestamp}{mb}{mp}
 ORDER BY pixels DESC
 LIMIT 201{start}""".format(
            **params
        ),
        queryArgs,
    )


def get(args):
    sql = makeQuery(args)
    if not sql:
        return
    commonsdb = DB()
    data = commonsdb.query(*sql)
    return [
        (i[0].decode("utf-8"), i[1], int(i[2]), int(i[3]), i[4], i[5], i[6])
        for i in data
    ]


def minmax(pmin, pmax, prefix, func=None):
    pmin = (func(pmin) if func else pmin) if pmin and pmin.isdigit() else ""
    pmax = (func(pmax) if func else pmax) if pmax and pmax.isdigit() else ""
    if pmin:
        if pmax:
            expr = " BETWEEN {} AND {}".format(pmin, pmax)
        else:
            expr = " >= {}".format(m[0])  # noqa
    else:
        if pmin:
            expr = " <= {}".format(m[1])  # noqa
        else:
            expr = ""
    return expr and prefix + expr
