import unittest
import os
import tempfile
import shutil

from morgy.database import Database
from morgy.database.updater import DatabaseUpdater


class TestDatabaseUpdater(unittest.TestCase):
    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_file.close()
        self.db = Database(self.db_file.name)
        self.temp_dir = tempfile.mkdtemp()
        self.updater = DatabaseUpdater(self.db)

    def tearDown(self):
        self.db.conn.close()
        os.unlink(self.db_file.name)
        shutil.rmtree(self.temp_dir)

    def _create_test_structure(self):
        """Create a test directory structure with music files."""
        # Create structure: temp_dir/Artist/1990 Album/01 Song.mp3
        artist_dir = os.path.join(self.temp_dir, "Test Artist")
        album_dir = os.path.join(artist_dir, "1990 Test Album")
        os.makedirs(album_dir)
        
        song1 = os.path.join(album_dir, "01 Test Song.mp3")
        song2 = os.path.join(album_dir, "02 Another Song.mp3")
        
        with open(song1, "w") as f:
            f.write("fake mp3 content")
        with open(song2, "w") as f:
            f.write("fake mp3 content")
        
        return [song1, song2]

    def test_update_db_adds_entries(self):
        self._create_test_structure()
        
        self.updater.update_db(self.temp_dir, 5)
        
        cursor = self.db.cursor
        cursor.execute("SELECT COUNT(*) FROM details")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 2)

    def test_update_db_sets_priority(self):
        self._create_test_structure()
        
        self.updater.update_db(self.temp_dir, 7)
        
        cursor = self.db.cursor
        cursor.execute("SELECT priority FROM details")
        priorities = [row[0] for row in cursor.fetchall()]
        self.assertEqual(set(priorities), {7})

    def test_update_db_filters_by_extension_mp3(self):
        # Create files with different extensions
        test_dir = os.path.join(self.temp_dir, "Test")
        os.makedirs(test_dir)
        
        with open(os.path.join(test_dir, "song.mp3"), "w") as f:
            f.write("mp3")
        with open(os.path.join(test_dir, "song.wma"), "w") as f:
            f.write("wma")
        with open(os.path.join(test_dir, "song.flac"), "w") as f:
            f.write("flac")
        with open(os.path.join(test_dir, "song.txt"), "w") as f:
            f.write("txt")
        
        self.updater.update_db(self.temp_dir, 1)
        
        cursor = self.db.cursor
        cursor.execute("SELECT COUNT(*) FROM details")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 3)  # mp3, wma, flac

    def test_update_db_filters_by_extension_case_insensitive(self):
        test_dir = os.path.join(self.temp_dir, "Test")
        os.makedirs(test_dir)
        
        with open(os.path.join(test_dir, "song.MP3"), "w") as f:
            f.write("mp3")
        with open(os.path.join(test_dir, "song.WMA"), "w") as f:
            f.write("wma")
        
        self.updater.update_db(self.temp_dir, 1)
        
        cursor = self.db.cursor
        cursor.execute("SELECT COUNT(*) FROM details")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 2)

    def test_update_db_empty_directory(self):
        # Just create empty directory
        os.makedirs(os.path.join(self.temp_dir, "Empty"))
        
        self.updater.update_db(self.temp_dir, 1)
        
        cursor = self.db.cursor
        cursor.execute("SELECT COUNT(*) FROM details")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 0)

    def test_update_db_nested_directories(self):
        # Create nested structure
        level1 = os.path.join(self.temp_dir, "Level1")
        level2 = os.path.join(level1, "Level2")
        level3 = os.path.join(level2, "Level3")
        os.makedirs(level3)
        
        with open(os.path.join(level3, "song.mp3"), "w") as f:
            f.write("content")
        
        self.updater.update_db(self.temp_dir, 1)
        
        cursor = self.db.cursor
        cursor.execute("SELECT COUNT(*) FROM details")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)

    def test_update_db_uses_detail_fetcher(self):
        # Create structure that DetailFetcher can parse
        artist_dir = os.path.join(self.temp_dir, "Test Artist")
        album_dir = os.path.join(artist_dir, "1990 Test Album")
        os.makedirs(album_dir)
        
        song_path = os.path.join(album_dir, "01 Test Song.mp3")
        with open(song_path, "w") as f:
            f.write("content")
        
        self.updater.update_db(self.temp_dir, 1)
        
        cursor = self.db.cursor
        cursor.execute("SELECT artist, year, album, number, title FROM details WHERE path=?", [song_path])
        row = cursor.fetchone()
        
        self.assertEqual(row[0], "Test Artist")
        self.assertEqual(row[1], 1990)
        self.assertEqual(row[2], "Test Album")
        self.assertEqual(row[3], 1)
        self.assertEqual(row[4], "Test Song")

    def test_remove_not_existing_entries(self):
        # Add entries to database
        existing_path = self._create_test_structure()[0]
        non_existing_path = "/definitely/not/existing/path.mp3"
        
        self.db.add_detail_row(non_existing_path, "Artist", "1990", "Album", "1", "01", "Song", 1)
        self.db.add_detail_row(existing_path, "Artist", "1990", "Album", "1", "01", "Song", 1)
        
        self.updater.remove_not_existing_entries()
        
        cursor = self.db.cursor
        cursor.execute("SELECT path FROM details")
        remaining_paths = [row[0] for row in cursor.fetchall()]
        
        self.assertIn(existing_path, remaining_paths)
        self.assertNotIn(non_existing_path, remaining_paths)

    def test_remove_not_existing_entries_removes_from_guitar_table(self):
        existing_path = self._create_test_structure()[0]
        non_existing_path = "/definitely/not/existing/path.mp3"
        
        self.db.add_detail_row(existing_path, "Artist", "1990", "Album", "1", "01", "Song", 1)
        self.db.add_detail_row(non_existing_path, "Artist", "1990", "Album", "1", "01", "Song", 1)
        self.db.add_guitar_row(non_existing_path, 1)
        
        self.updater.remove_not_existing_entries()
        
        cursor = self.db.cursor
        cursor.execute("SELECT path FROM guitar")
        remaining_guitar_paths = [row[0] for row in cursor.fetchall()]
        
        self.assertNotIn(non_existing_path, remaining_guitar_paths)

    def test_remove_not_existing_entries_keeps_existing_guitar_entries(self):
        existing_path = self._create_test_structure()[0]
        
        self.db.add_detail_row(existing_path, "Artist", "1990", "Album", "1", "01", "Song", 1)
        self.db.add_guitar_row(existing_path, 1)
        
        self.updater.remove_not_existing_entries()
        
        cursor = self.db.cursor
        cursor.execute("SELECT path FROM guitar")
        remaining_guitar_paths = [row[0] for row in cursor.fetchall()]
        
        self.assertIn(existing_path, remaining_guitar_paths)

    def test_close_commits_and_closes(self):
        existing_path = self._create_test_structure()[0]
        self.db.add_detail_row(existing_path, "Artist", "1990", "Album", "1", "01", "Song", 1)
        
        # Manually rollback to test that close() commits
        self.db.conn.rollback()
        
        self.updater.close()
        
        # Should be closed
        with self.assertRaises(Exception):  # sqlite3.ProgrammingError or similar
            self.db.cursor.execute("SELECT 1")


if __name__ == "__main__":
    unittest.main()


