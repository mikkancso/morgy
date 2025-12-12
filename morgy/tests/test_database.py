import unittest
import os
import sqlite3
import tempfile

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
        self.db_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_file.close()
        self.db = Database(self.db_file.name)
        # Populate with test data instead of copying production DB
        self._populate_test_data()

    def tearDown(self):
        self.db.conn.close()
        os.unlink(self.db_file.name)

    def _populate_test_data(self):
        """Populate database with known test data."""
        test_rows = [
            ("/path/to/song1.mp3", "Artist One", "1990", "Album One", "1", "01", "Song One", 5),
            ("/path/to/song2.mp3", "Artist Two", "1991", "Album Two", None, "02", "Song Two", 3),
            ("/path/to/song3.mp3", "Artist One", "1992", "Album Three", "2", "03", "Song Three", 7),
        ]
        for row in test_rows:
            self.db.add_detail_row(*row)
        # Add some guitar entries
        self.db.add_guitar_row("/path/to/song1.mp3", 1)
        self.db.add_guitar_row("/path/to/song3.mp3", 1)

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

    def test_get_all_guitar_paths(self):
        paths = list(self.db.get_all_guitar_paths())
        self.assertEqual(len(paths), 2)
        path_tuples = [p[0] for p in paths]
        self.assertIn("/path/to/song1.mp3", path_tuples)
        self.assertIn("/path/to/song3.mp3", path_tuples)

    def test_get_all_guitar_paths_empty(self):
        # Create fresh DB with no guitar entries
        db_file = tempfile.NamedTemporaryFile(delete=False)
        db_file.close()
        db = Database(db_file.name)
        paths = list(db.get_all_guitar_paths())
        self.assertEqual(paths, [])
        db.conn.close()
        os.unlink(db_file.name)

    def test_delete_entry_with_path(self):
        self.db.delete_entry_with_path("/path/to/song2.mp3")
        result = self.query("SELECT path FROM details WHERE path=?", ["/path/to/song2.mp3"])
        self.assertEqual(len(result), 0)

    def test_delete_entry_with_path_like_pattern(self):
        # Test LIKE pattern matching
        self.db.delete_entry_with_path("%song1%")
        result = self.query("SELECT path FROM details WHERE path LIKE ?", ["%song1%"])
        self.assertEqual(len(result), 0)

    def test_delete_entry_with_path_cascades_to_guitar(self):
        # Delete a detail entry that has a guitar entry
        # Foreign key should cascade delete
        self.db.delete_entry_with_path("/path/to/song1.mp3")
        result = self.query("SELECT path FROM guitar WHERE path=?", ["/path/to/song1.mp3"])
        self.assertEqual(len(result), 0)

    def test_delete_entry_with_path_from_guitar(self):
        self.db.delete_entry_with_path_from_guitar("/path/to/song1.mp3")
        result = self.query("SELECT path FROM guitar WHERE path=?", ["/path/to/song1.mp3"])
        self.assertEqual(len(result), 0)
        # Details entry should still exist
        result = self.query("SELECT path FROM details WHERE path=?", ["/path/to/song1.mp3"])
        self.assertEqual(len(result), 1)

    def test_delete_entry_with_path_from_guitar_like_pattern(self):
        self.db.delete_entry_with_path_from_guitar("%song1%")
        result = self.query("SELECT path FROM guitar WHERE path LIKE ?", ["%song1%"])
        self.assertEqual(len(result), 0)

    def test_commit_and_close(self):
        # Add a row and commit/close
        self.db.add_detail_row("test_path", "Artist", "1990", "Album", "1", "01", "Title", 1)
        self.db.commit_and_close()
        
        # Reopen and verify
        db = Database(self.db_file.name)
        cursor = db.cursor
        cursor.execute("SELECT path FROM details WHERE path=?", ["test_path"])
        result = cursor.fetchall()
        self.assertEqual(len(result), 1)
        db.conn.close()

    def test_add_detail_row_duplicate_path(self):
        # Adding same path twice should not raise, just print message
        self.db.add_detail_row("duplicate_path", "Artist", "1990", "Album", "1", "01", "Title", 1)
        # Should not raise exception
        try:
            self.db.add_detail_row("duplicate_path", "Artist", "1990", "Album", "1", "01", "Title", 1)
        except sqlite3.IntegrityError:
            self.fail("add_detail_row should catch IntegrityError")
        
        # Should only have one entry
        result = self.query("SELECT COUNT(*) FROM details WHERE path=?", ["duplicate_path"])
        self.assertEqual(result[0][0], 1)

    def test_get_rows_from_table_guitar(self):
        rows = list(self.db.get_rows_from_table("guitar"))
        self.assertEqual(len(rows), 2)
        # Each row should be (path, guitar)
        for row in rows:
            self.assertEqual(len(row), 2)

    def test_get_rows_from_table_empty(self):
        db_file = tempfile.NamedTemporaryFile(delete=False)
        db_file.close()
        db = Database(db_file.name)
        rows = list(db.get_rows_from_table("details"))
        self.assertEqual(rows, [])
        db.conn.close()
        os.unlink(db_file.name)

    def test_get_path_where_empty_result(self):
        paths = list(self.db.get_path_where("artist='Nonexistent Artist'"))
        self.assertEqual(paths, [])

    def test_get_path_where_multiple_results(self):
        paths = list(self.db.get_path_where("artist='Artist One'"))
        self.assertEqual(len(paths), 2)
        path_values = [p[0] for p in paths]
        self.assertIn("/path/to/song1.mp3", path_values)
        self.assertIn("/path/to/song3.mp3", path_values)

    def test_decrease_prio_like_pattern(self):
        # Test that LIKE pattern works in decrease_prio
        self.db.add_detail_row("/test/song.mp3", "Artist", "1990", "Album", "1", "01", "Title", 5)
        self.db.decrease_prio("%song%")
        result = self.query("SELECT priority FROM details WHERE path=?", ["/test/song.mp3"])
        self.assertEqual(result[0][0], 4)

    def test_decrease_prio_multiple_matches(self):
        # Add multiple paths matching pattern
        self.db.add_detail_row("/test/song1.mp3", "Artist", "1990", "Album", "1", "01", "Title", 5)
        self.db.add_detail_row("/test/song2.mp3", "Artist", "1990", "Album", "1", "02", "Title", 3)
        self.db.decrease_prio("%song%")
        result1 = self.query("SELECT priority FROM details WHERE path=?", ["/test/song1.mp3"])
        result2 = self.query("SELECT priority FROM details WHERE path=?", ["/test/song2.mp3"])
        self.assertEqual(result1[0][0], 4)
        self.assertEqual(result2[0][0], 2)


if __name__ == "__main__":
    unittest.main()
