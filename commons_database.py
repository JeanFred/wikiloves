#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time

import pymysql


class DB:
    """
    Classe para fazer consultas ao banco de dados
    """

    def connect(self):
        username = os.environ.get("DB_USERNAME", None)
        password = os.environ.get("DB_PASSWORD", None)
        host = os.environ.get("DB_HOST", "commonswiki.analytics.db.svc.eqiad.wmflabs")
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
        loops = 0
        self.connect()
        while True:
            try:
                return self._query(*sql)
            except (AttributeError, pymysql.err.OperationalError):
                if loops < 10:
                    loops += 1
                    print("Erro no DB, esperando %ds antes de tentar de novo" % loops)
                    time.sleep(loops)
                else:
                    return self._query(*sql)
                    break
            else:
                print("Uncaught exception when running query")
                print(sql)
                break
        self.close_connection()

    def close_connection(self):
        self.conn.close()
