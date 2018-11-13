import unittest
import os
import shutil
import sqlite3
import tempfile
import configparser
from .. import CONFIG_FILE

from morgy.database import Database


class TestNewDatabase(unittest.TestCase):
    def setUp(self):
        pass

    def test_schema_is_created_upon_creating_a_new_db(self):
        with tempfile.NamedTemporaryFile() as db:
            new_db = Database(db.name)
            new_db.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' or type='view'"
            )
            existing_tables = new_db.cursor.fetchall()
            self.assertTrue(("details",) in existing_tables)
            self.assertTrue(("guitar",) in existing_tables)


class TestExistingDatabase(unittest.TestCase):
    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile()
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        shutil.copyfile(config["DEFAULT"]["database_path"], self.db_file.name)
        self.db = Database(self.db_file.name)

    def tearDown(self):
        self.db_file.close()

    def query(self, query, values=[]):
        self.db.cursor.execute(query, values)
        return self.db.cursor.fetchall()

    def test_no_new_tables_are_created(self):
        existing_tables = self.query(
            "SELECT name FROM sqlite_master WHERE type='table' or type='view'"
        )
        self.assertTrue(("details",) in existing_tables)
        self.assertTrue(("guitar",) in existing_tables)
        self.assertEqual(len(existing_tables), 2)
        self.assertEqual(len(existing_tables[0]), 1)

    def test_querying_an_added_row(self):
        row_details = ("path", "artist", "1990", "album", "1", "02", "title", 3)
        expected = ("path", "artist", 1990, "album", 1, 2, "title", 3)
        self.db.add_detail_row(*row_details)
        result = self.query("SELECT * FROM details WHERE path='path'")
        self.assertEqual(expected, result[0])

    def test_querying_an_added_guitar_row(self):
        row_details = ("path", "artist", "1990", "album", "1", "02", "title", 3)
        self.db.add_detail_row(*row_details)
        self.db.add_guitar_row("path", 1)
        result = self.query("SELECT * FROM guitar WHERE path='path'")
        self.assertEqual(("path", 1), result[0])

    def test_get_title_path_and_prio_returns_valid_data(self):
        data = self.db.get_title_path_and_prio()
        (title, path, prio) = next(data)
        result = self.query(
            "SELECT title, path, priority FROM details WHERE path=(?)", [path]
        )
        self.assertEqual((title, path, prio), result[0])

    def test_get_rows_returns_valid_data(self):
        data = self.db.get_rows_from_table("details")
        row = next(data)
        result = self.query("SELECT * FROM details WHERE path=(?)", [row[0]])
        self.assertEqual(row, result[0])

    def test_get_path_where_returns_valid_data(self):
        data = self.db.get_rows_from_table("details")
        (path, artist, _, _, _, _, title, _) = next(data)
        where_clause = "artist='{}' AND title='{}'".format(artist, title)
        expected_path = next(self.db.get_path_where(where_clause))
        self.assertEqual(path, expected_path[0])

    def decrease_a_prio(self, priority):
        row_details = ("path", "artist", "1990", "album", "1", "02", "title", priority)
        self.db.add_detail_row(*row_details)
        self.db.decrease_prio("path")
        prio = self.query("SELECT priority FROM details WHERE path='path'")
        return prio[0][0]

    def test_decreasing_a_prio_from_2(self):
        self.assertEqual(self.decrease_a_prio(2), 1)

    def test_decreasing_a_prio_from_10(self):
        self.assertEqual(self.decrease_a_prio(10), 9)

    def test_decreasing_a_prio_from_1_doesnt_change(self):
        self.assertEqual(self.decrease_a_prio(1), 1)

    def decrease_a_prio_then_close_and_open_works(self):
        self.decrease_a_prio(10)
        self.db.commit_and_close()
        self.db = Database(self.db_file.name)
        prio = self.query("SELECT priority FROM details WHERE path='path'")
        self.assertEqual(prio, 9)

    def test_adding_a_guitar_row_twice(self):
        row_details = ("path", "artist", "1990", "album", "1", "02", "title", 3)
        self.db.add_detail_row(*row_details)
        self.db.add_guitar_row("path", 1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add_guitar_row("path", 1)

    def test_adding_a_non_existent_path_to_guitar_table(self):
        row_details = ("path", "artist", "1990", "album", "1", "02", "title", 3)
        self.db.add_detail_row(*row_details)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add_guitar_row("definitely not existing", 1)


if __name__ == "__main__":
    unittest.main()
