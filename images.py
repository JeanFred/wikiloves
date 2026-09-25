# -*- coding: utf-8  -*-

from commons_database import DB, TITLE_CHUNK_SIZE, as_text, chunked
from functions import get_wikiloves_category_name, normalize_country_name

# Result page size (the query returns at most this many rows).
PAGE_SIZE = 201


def make_category_query(category):
    """Resolve a category to the titles of the files it contains (links cluster)."""
    return (
        """SELECT page_title
 FROM categorylinks
 INNER JOIN page ON cl_from = page_id
 WHERE cl_target_id = (SELECT lt_id FROM linktarget WHERE lt_title = %s AND lt_namespace = 14)
   AND cl_type = 'file'""",
        (category,),
    )


def make_image_query(titles, args, limit):
    """Top image/actor metadata for the given file titles (core cluster).

    Applies the user/size/megapixel/timestamp filters and returns up to
    ``limit`` rows ordered by pixels. Offset/paging is applied by the caller
    after merging chunks, so it is deliberately not part of this query.
    """
    params = {}
    params["titles"] = ", ".join(["%s"] * len(titles))
    queryArgs = tuple(titles)

    params["user"] = " AND actor_name = %s" if "user" in args else ""
    if params["user"]:
        queryArgs += (args["user"].replace("_", " "),)
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
    params["limit"] = limit
    return (
        """SELECT
 img_name,
 SUBSTR(MD5(img_name), 1, 2),
 img_width,
 img_height,
 (img_width * img_height) pixels,
 img_size,
 img_timestamp
 FROM image
 INNER JOIN actor_image ON actor_image.actor_id = image.img_actor
 WHERE img_name IN ({titles}) AND img_major_mime = 'image'{user}{timestamp}{mb}{mp}
 ORDER BY pixels DESC
 LIMIT {limit}""".format(
            **params
        ),
        queryArgs,
    )


def get(args):
    if not ("event" in args and "year" in args and "country" in args):
        return
    country = normalize_country_name(args["country"])
    category = get_wikiloves_category_name(args["event"].title(), args["year"], country)
    start = int(args["start"]) if str(args.get("start", "")).isdigit() else 0

    # Step 1: resolve the category to file titles on the links cluster.
    with DB(links=True) as linksdb:
        titles = [
            as_text(row[0]) for row in linksdb.query(*make_category_query(category))
        ]
    if not titles:
        return []

    # Step 2: fetch image/actor metadata on the core cluster. The title list is
    # chunked so large categories stay under the statement-size limit; each
    # chunk returns its own top PAGE_SIZE, which together contain the global top
    # PAGE_SIZE once merged and re-sorted. Offset/paging is applied here.
    rows = []
    with DB() as commonsdb:
        for batch in chunked(titles, TITLE_CHUNK_SIZE):
            rows += commonsdb.query(*make_image_query(batch, args, start + PAGE_SIZE))
    rows.sort(key=lambda r: r[4], reverse=True)

    return [
        (as_text(i[0]), i[1], int(i[2]), int(i[3]), i[4], i[5], i[6])
        for i in rows[start : start + PAGE_SIZE]
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
