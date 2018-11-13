import sqlite3
import configparser
from morgy import CONFIG_FILE


class Database:
    def __init__(self, path=None):
        if not path:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            path = config["DEFAULT"]["database_path"]

        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys = 1")
        self.cursor = self.conn.cursor()
        self.create_new_tables()

    def create_new_tables(self):
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' or type='view'"
        )
        existing_tables = self.cursor.fetchall()
        if ("details",) not in existing_tables:
            self.cursor.execute(
                """CREATE TABLE details(
                path text primary key not null,
                artist text,
                year int,
                album text,
                cd_number int,
                number int,
                title text not null,
                priority int not null
                )"""
            )
            self.conn.commit()
        if ("guitar",) not in existing_tables:
            self.cursor.execute(
                """CREATE TABLE guitar(
                path text primary key not null,
                guitar int,
                FOREIGN KEY(path) REFERENCES details(path)
                )"""
            )
            self.conn.commit()

    # FIXME: Do we use it? Do we want to?
    def commit_and_close(self):
        self.conn.commit()
        self.conn.close()

    def add_detail_row(
        self, path, artist, year, album, cd_number, number, title, priority
    ):
        values = [path, artist, year, album, cd_number, number, title, priority]
        try:
            self.cursor.execute("INSERT INTO details VALUES (?,?,?,?,?,?,?,?)", values)
            self.conn.commit()
        # FIXME: is this the best behaviour?
        except sqlite3.IntegrityError:
            print("most likely has already been added")

    def add_guitar_row(self, path, guitar):
        values = [path, guitar]
        self.cursor.execute("INSERT INTO guitar VALUES (?,?)", values)
        self.conn.commit()

    def get_title_path_and_prio(self):
        self.cursor.execute("SELECT title, path, priority FROM details")
        while True:
            results = self.cursor.fetchmany()
            if not results:
                break
            for result in results:
                yield result

    def get_rows_from_table(self, table):
        self.cursor.execute("SELECT * FROM {}".format(table))
        while True:
            results = self.cursor.fetchmany()
            if not results:
                break
            for result in results:
                yield result

    def get_path_where(self, where):
        # FIXME: SQLi
        self.cursor.execute("SELECT path FROM details WHERE {}".format(where))
        while True:
            results = self.cursor.fetchmany()
            if not results:
                break
            for result in results:
                yield result

    def decrease_prio(self, path):
        path = [path]
        self.cursor.execute(
            "UPDATE details SET priority = priority - 1 WHERE path LIKE (?) AND priority > 1",
            path,
        )

    def delete_entry_with_path(self, path):
        path = [path]
        self.cursor.execute("DELETE FROM details WHERE path LIKE (?)", path)

    def delete_entry_with_path_from_guitar(self, path):
        path = [path]
        self.cursor.execute("DELETE FROM guitar WHERE path LIKE (?)", path)
        self.conn.commit()
