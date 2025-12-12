import unittest
import os
import shutil
import tempfile

from morgy.smart_picker import SmartPicker
from morgy.database import Database


class TestSmartPicker(unittest.TestCase):
    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_file.close()
        self.db = Database(self.db_file.name)
        self.smart_picker = SmartPicker(self.db)
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []

    def tearDown(self):
        self.db.conn.close()
        os.unlink(self.db_file.name)
        shutil.rmtree(self.temp_dir)

    def _create_test_file(self, filename, size_bytes=1024):
        """Create a test file with specified size and return its path."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, "wb") as f:
            f.write(b"0" * size_bytes)
        self.test_files.append(filepath)
        return filepath

    def _add_row_with_defaults(
        self,
        path=None,
        artist="artist",
        year="1990",
        album="album",
        cd="1",
        number="01",
        title="title",
        prio="1",
    ):
        if path is None:
            path = self._create_test_file("test.mp3")
        row_details = (path, artist, year, album, cd, number, title, prio)
        self.db.add_detail_row(*row_details)
        return path

    def test_build_dict_from_database(self):
        path1 = self._add_row_with_defaults(title="Song One", prio="3")
        path2 = self._add_row_with_defaults(path=self._create_test_file("test2.mp3"), title="Song One", prio="5")
        path3 = self._add_row_with_defaults(path=self._create_test_file("test3.mp3"), title="Song Two", prio="2")
        
        titles = self.smart_picker.build_dict_from_database()
        
        self.assertIn("Song One", titles)
        self.assertIn("Song Two", titles)
        self.assertEqual(len(titles["Song One"]), 2)
        self.assertEqual(len(titles["Song Two"]), 1)
        self.assertIn((path1, 3), titles["Song One"])
        self.assertIn((path2, 5), titles["Song One"])
        self.assertIn((path3, 2), titles["Song Two"])

    def test_build_dict_from_database_removes_live_suffix(self):
        path1 = self._add_row_with_defaults(title="Song (live)", prio="1")
        path2 = self._add_row_with_defaults(path=self._create_test_file("test2.mp3"), title="Song", prio="2")
        
        titles = self.smart_picker.build_dict_from_database()
        
        # Both should be grouped under "Song" (without "(live)")
        self.assertIn("Song", titles)
        self.assertEqual(len(titles["Song"]), 2)

    def test_build_dict_from_database_empty_database(self):
        titles = self.smart_picker.build_dict_from_database()
        self.assertEqual(titles, {})

    def test_get_weighted_selected_paths(self):
        titles = {
            "title": [("path1", 1), ("path2", 2)],
            "other title": [("path3", 3)],
        }
        weighted_paths = self.smart_picker.get_weighted_selected_paths(titles)
        
        # Should have 1 + 2 + 3 = 6 paths total
        self.assertEqual(len(weighted_paths), 6)
        # Each path should appear priority times
        self.assertEqual(weighted_paths.count("path1"), 1)
        self.assertEqual(weighted_paths.count("path2"), 2)
        self.assertEqual(weighted_paths.count("path3"), 3)

    def test_get_weighted_selected_paths_single_path_per_title(self):
        titles = {
            "title1": [("path1", 5)],
            "title2": [("path2", 3)],
        }
        weighted_paths = self.smart_picker.get_weighted_selected_paths(titles)
        
        self.assertEqual(len(weighted_paths), 8)
        self.assertEqual(weighted_paths.count("path1"), 5)
        self.assertEqual(weighted_paths.count("path2"), 3)

    def test_pick_respects_quantity_limit(self):
        # Create files with known sizes
        path1 = self._create_test_file("file1.mp3", 500 * 1024)  # 500 KB
        path2 = self._create_test_file("file2.mp3", 300 * 1024)  # 300 KB
        path3 = self._create_test_file("file3.mp3", 200 * 1024)  # 200 KB
        
        self._add_row_with_defaults(path=path1, title="Song1", prio="1")
        self._add_row_with_defaults(path=path2, title="Song2", prio="1")
        self._add_row_with_defaults(path=path3, title="Song3", prio="1")
        
        result = self.smart_picker.pick(600 * 1024)
        
        self.assertIn(path1, result)
        total_size = sum(os.stat(p).st_size for p in result)
        self.assertLessEqual(total_size, (600 + 300) * 1024)

    def test_pick_no_duplicates(self):
        path1 = self._create_test_file("file1.mp3", 100 * 1024)
        path2 = self._create_test_file("file2.mp3", 100 * 1024)
        
        self._add_row_with_defaults(path=path1, title="Song1", prio="2")
        self._add_row_with_defaults(path=path2, title="Song2", prio="2")
        
        result = self.smart_picker.pick(500 * 1024)
        
        # Should not have duplicates
        self.assertEqual(len(result), len(set(result)))

    def test_pick_all_from_guitar(self):
        path1 = self._add_row_with_defaults(title="Song1")
        path2 = self._add_row_with_defaults(path=self._create_test_file("test2.mp3"), title="Song2")
        path3 = self._add_row_with_defaults(path=self._create_test_file("test3.mp3"), title="Song3")
        
        self.db.add_guitar_row(path1, 1)
        self.db.add_guitar_row(path3, 1)
        
        result = self.smart_picker.pick_all_from_guitar()
        
        self.assertEqual(len(result), 2)
        self.assertIn(path1, result)
        self.assertIn(path3, result)
        self.assertNotIn(path2, result)

    def test_pick_all_from_guitar_empty(self):
        result = self.smart_picker.pick_all_from_guitar()
        self.assertEqual(result, [])

    def test_decrease_prio(self):
        path1 = self._add_row_with_defaults(prio="5")
        path2 = self._add_row_with_defaults(path=self._create_test_file("test2.mp3"), prio="3")
        
        self.smart_picker.decrease_prio([path1, path2])
        
        # Reopen DB to verify changes persisted
        self.db.conn.close()
        self.db = Database(self.db_file.name)
        
        cursor = self.db.cursor
        cursor.execute("SELECT priority FROM details WHERE path=?", [path1])
        self.assertEqual(cursor.fetchone()[0], 4)
        
        cursor.execute("SELECT priority FROM details WHERE path=?", [path2])
        self.assertEqual(cursor.fetchone()[0], 2)

    def test_prepend_number(self):
        self.assertEqual(self.smart_picker.prepend_number("song.mp3", 0), "000_song.mp3")
        self.assertEqual(self.smart_picker.prepend_number("song.mp3", 42), "042_song.mp3")
        self.assertEqual(self.smart_picker.prepend_number("song.mp3", 999), "999_song.mp3")

    def test_copy_list_to_destination(self):
        dest_dir = tempfile.mkdtemp()
        try:
            path1 = self._create_test_file("song1.mp3", 100)
            path2 = self._create_test_file("song2.mp3", 200)
            
            self.smart_picker.copy_list_to_destination([path1, path2], dest_dir + os.sep)
            
            # Check files were copied with numbering
            self.assertTrue(os.path.exists(os.path.join(dest_dir, "000_song1.mp3")))
            self.assertTrue(os.path.exists(os.path.join(dest_dir, "001_song2.mp3")))
            
            # Check file contents
            with open(os.path.join(dest_dir, "000_song1.mp3"), "rb") as f:
                self.assertEqual(len(f.read()), 100)
        finally:
            shutil.rmtree(dest_dir)


if __name__ == "__main__":
    unittest.main()
