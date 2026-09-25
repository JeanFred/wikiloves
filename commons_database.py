#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time

import pymysql


# Cap on how many titles go into a single IN (...) clause, to stay well under
# the server's statement-size limit for very large categories.
TITLE_CHUNK_SIZE = 5000


def as_text(value):
    """Normalize a DB value (bytes or str) to str for cross-cluster joins."""
    return value.decode("utf-8") if isinstance(value, bytes) else value


def chunked(seq, size):
    """Yield successive ``size``-length slices of ``seq``."""
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


# Default hostnames for the two Commons wiki replica clusters.
# As of the 2026 Commons links tables database split, the links tables
# (categorylinks, linktarget, globalimagelinks, pagelinks, ...) live on a
# separate `x4` cluster reachable via a dedicated `links.` hostname, and can
# no longer be JOINed against the core (`s4`) tables (image, actor, user, ...).
# See https://wikitech.wikimedia.org/wiki/News/2026_Commons_links_tables_database_split
DEFAULT_CORE_HOST = "commonswiki.analytics.db.svc.wikimedia.cloud"
DEFAULT_LINKS_HOST = "links.commonswiki.analytics.db.svc.wikimedia.cloud"


class DB:
    """
    Classe para fazer consultas ao banco de dados

    ``links=True`` connects to the `x4` links cluster (categorylinks,
    linktarget, globalimagelinks, ...); the default connects to the core
    cluster (image, actor, user, page, ...).
    """

    def __init__(self, links=False):
        self.links = links

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_connection()

    def connect(self):
        # Close any existing connection before opening a new one, so that
        # reconnection attempts do not leak connections (max_user_connections).
        self.close_connection()

        username = os.environ.get("DB_USERNAME", None)
        password = os.environ.get("DB_PASSWORD", None)
        if self.links:
            host = os.environ.get("DB_LINKS_HOST", DEFAULT_LINKS_HOST)
        else:
            host = os.environ.get("DB_HOST", DEFAULT_CORE_HOST)
        self.conn = pymysql.connect(
            db="commonswiki_p",
            host=host,
            user=username,
            passwd=password,
            read_default_file=os.path.expanduser("~/replica.my.cnf"),
            read_timeout=30,
            charset="utf8",
            use_unicode=True,
        )
        self.conn.ping(True)

    def _query(self, *sql):
        with self.conn.cursor() as cursor:
            cursor.execute(*sql)
            return cursor.fetchall()

    def query(self, *sql):
        """
        Tenta fazer a consulta, reconecta até 10 vezes até conseguir
        """
        if not getattr(self, "conn", None):
            self.connect()

        loops = 0
        while True:
            try:
                return self._query(*sql)
            except (AttributeError, pymysql.err.OperationalError):
                if loops < 10:
                    loops += 1
                    print("Erro no DB, esperando %ds antes de tentar de novo" % loops)
                    time.sleep(loops)
                    self.connect()
                else:
                    raise

    def close_connection(self):
        conn = getattr(self, "conn", None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
            self.conn = None
