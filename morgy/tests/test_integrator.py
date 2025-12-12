import unittest
import os
import shutil
import tempfile
from unittest.mock import patch

from morgy.database import Database
from morgy.integrator import Integrator


class TestIntegrator(unittest.TestCase):
    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_file.close()
        self.db = Database(self.db_file.name)
        
        self.temp_dir = tempfile.mkdtemp()
        self.to_integrate = os.path.join(self.temp_dir, "to_integrate")
        self.destination = os.path.join(self.temp_dir, "destination")
        os.makedirs(self.to_integrate)
        os.makedirs(self.destination)
        
        # Create test structure: leaf directory with files
        self.leaf_dir = os.path.join(self.to_integrate, "Artist", "1990 Album")
        os.makedirs(self.leaf_dir)
        
        # Create test music files
        self.song1 = os.path.join(self.leaf_dir, "01_song_one.mp3")
        self.song2 = os.path.join(self.leaf_dir, "02_song_two.mp3")
        with open(self.song1, "w") as f:
            f.write("fake mp3 content")
        with open(self.song2, "w") as f:
            f.write("fake mp3 content")

    def tearDown(self):
        self.db.conn.close()
        os.unlink(self.db_file.name)
        shutil.rmtree(self.temp_dir)

    @patch('builtins.input', return_value='')
    @patch('os.system')
    def test_ask_for_path(self, mock_system, mock_input):
        """Test that ask_for_path collects destination paths."""
        integrator = Integrator(self.to_integrate, self.db)
        
        # Mock input to return a valid directory
        with patch('builtins.input', return_value=self.destination):
            with patch('os.path.isdir', return_value=True):
                integrator.ask_for_path(self.leaf_dir)
        
        self.assertIn(self.leaf_dir, integrator.info)
        self.assertEqual(integrator.info[self.leaf_dir]["path"], os.path.realpath(self.destination))

    def test_move(self):
        """Test that move relocates directories correctly."""
        integrator = Integrator(self.to_integrate, self.db)
        dest_subdir = os.path.join(self.destination, "Artist", "1990 Album")
        os.makedirs(dest_subdir, exist_ok=True)
        
        integrator.info[self.leaf_dir] = {"path": self.destination}
        integrator.move(self.leaf_dir)
        
        # Original should be gone
        self.assertFalse(os.path.exists(self.leaf_dir))
        # New location should exist
        self.assertTrue(os.path.exists(dest_subdir))
        # Files should be in new location
        self.assertTrue(os.path.exists(os.path.join(dest_subdir, "01_song_one.mp3")))

    @patch('builtins.input')
    @patch('os.system')
    def test_run_full_workflow(self, mock_system, mock_input):
        """Test the full integration workflow."""
        # Mock input for ask_for_path
        def input_side_effect(prompt):
            if "Destination folder" in prompt:
                return self.destination
            return ""
        
        mock_input.side_effect = input_side_effect
        mock_system.return_value = None  # Mock vim call
        
        integrator = Integrator(self.to_integrate, self.db)
        integrator.run()
        
        # Verify files were moved
        dest_leaf = os.path.join(self.destination, "Artist", "1990 Album")
        self.assertTrue(os.path.exists(dest_leaf))
        
        # Verify database was updated
        cursor = self.db.cursor
        cursor.execute("SELECT COUNT(*) FROM details")
        count = cursor.fetchone()[0]
        self.assertGreater(count, 0)

    @patch('builtins.input')
    @patch('os.system')
    def test_run_creates_recommendations(self, mock_system, mock_input):
        """Test that recommendations file is created and used."""
        def input_side_effect(prompt):
            if "Destination folder" in prompt:
                return self.destination
            return ""
        
        mock_input.side_effect = input_side_effect
        mock_system.return_value = None
        
        integrator = Integrator(self.to_integrate, self.db)
        integrator.run()
        
        # Verify vim was called (for editing recommendations)
        self.assertTrue(mock_system.called)

    def test_run_finds_leaf_directories(self):
        """Test that only leaf directories (with files, no subdirs) are processed."""
        # Create nested structure
        nested_dir = os.path.join(self.to_integrate, "Nested", "Level1", "Level2")
        os.makedirs(nested_dir)
        with open(os.path.join(nested_dir, "song.mp3"), "w") as f:
            f.write("content")
        
        # Create non-leaf directory (has subdirs)
        non_leaf = os.path.join(self.to_integrate, "NonLeaf")
        os.makedirs(non_leaf)
        os.makedirs(os.path.join(non_leaf, "subdir"))
        with open(os.path.join(non_leaf, "song.mp3"), "w") as f:
            f.write("content")
        
        with patch('builtins.input', return_value=self.destination):
            with patch('os.path.isdir', return_value=True):
                with patch('os.system'):
                    integrator = Integrator(self.to_integrate, self.db)
                    integrator.run()
        
        # Only leaf directories should be in info
        self.assertIn(self.leaf_dir, integrator.info)
        self.assertIn(nested_dir, integrator.info)
        # Non-leaf should not be processed (has subdirs)
        self.assertNotIn(non_leaf, integrator.info)


class TestIntegratorWorkflows(unittest.TestCase):
    """Integration tests for complete workflows."""
    
    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_file.close()
        self.db = Database(self.db_file.name)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        self.db.conn.close()
        os.unlink(self.db_file.name)
        shutil.rmtree(self.temp_dir)

    def test_sanitize_to_rename_workflow(self):
        """Test complete workflow: sanitize → rename."""
        from morgy.song_cleankeeper.path_sanitizer import PathSanitizer
        from morgy.song_cleankeeper.renamer import Renamer
        
        # Create test files
        test_dir = os.path.join(self.temp_dir, "test_music")
        os.makedirs(test_dir)
        
        old_file1 = os.path.join(test_dir, "01_TEST_SONG-NAME.mp3")
        old_file2 = os.path.join(test_dir, "02_ANOTHER-SONG.mp3")
        with open(old_file1, "w") as f:
            f.write("content1")
        with open(old_file2, "w") as f:
            f.write("content2")
        
        # Step 1: Generate recommendations
        recommendations_file = os.path.join(self.temp_dir, "recommendations.txt")
        ps = PathSanitizer()
        ps.write_recommendations(test_dir, recommendations_file)
        
        # Verify recommendations file exists and has content
        self.assertTrue(os.path.exists(recommendations_file))
        with open(recommendations_file, "r") as f:
            content = f.read()
            self.assertIn("01_TEST_SONG-NAME.mp3", content)
        
        # Step 2: Apply renaming
        renamer = Renamer()
        renamer.apply_recommendations(recommendations_file)
        
        # Verify files were renamed (check that old names don't exist)
        # Note: exact new names depend on PathSanitizer processing
        # But we can verify the old underscore/dash format is gone
        files_after = os.listdir(test_dir)
        self.assertNotIn("01_TEST_SONG-NAME.mp3", files_after)
        self.assertNotIn("02_ANOTHER-SONG.mp3", files_after)
        # Should have new names
        self.assertEqual(len([f for f in files_after if f.endswith(".mp3")]), 2)

    def test_update_to_query_workflow(self):
        """Test complete workflow: update database → query results."""
        from morgy.database.updater import DatabaseUpdater
        
        # Create test music structure
        music_dir = os.path.join(self.temp_dir, "music")
        artist_dir = os.path.join(music_dir, "Test Artist")
        album_dir = os.path.join(artist_dir, "1990 Test Album")
        os.makedirs(album_dir)
        
        song1 = os.path.join(album_dir, "01 Test Song.mp3")
        song2 = os.path.join(album_dir, "02 Another Song.mp3")
        with open(song1, "w") as f:
            f.write("content1")
        with open(song2, "w") as f:
            f.write("content2")
        
        # Step 1: Update database
        updater = DatabaseUpdater(self.db)
        updater.update_db(music_dir, 5)
        
        # Step 2: Query results
        cursor = self.db.cursor
        cursor.execute("SELECT path, artist, year, title FROM details")
        results = cursor.fetchall()
        
        # Verify data
        self.assertEqual(len(results), 2)
        paths = [r[0] for r in results]
        self.assertIn(song1, paths)
        self.assertIn(song2, paths)
        
        # Verify metadata
        for row in results:
            path, artist, year, title = row
            if path == song1:
                self.assertEqual(artist, "Test Artist")
                self.assertEqual(year, 1990)
                self.assertEqual(title, "Test Song")

    def test_smart_picker_to_copy_workflow(self):
        """Test workflow: smart pick → decrease priority → copy files."""
        from morgy.smart_picker import SmartPicker
        
        # Create test files with known sizes
        music_dir = os.path.join(self.temp_dir, "music")
        os.makedirs(music_dir)
        
        file1 = os.path.join(music_dir, "song1.mp3")
        file2 = os.path.join(music_dir, "song2.mp3")
        with open(file1, "wb") as f:
            f.write(b"0" * (200 * 1024))  # 200 KB
        with open(file2, "wb") as f:
            f.write(b"0" * (300 * 1024))  # 300 KB
        
        # Add to database
        self.db.add_detail_row(file1, "Artist1", "1990", "Album1", "1", "01", "Song1", 3)
        self.db.add_detail_row(file2, "Artist2", "1991", "Album2", "1", "02", "Song2", 5)
        
        # Step 1: Smart pick
        picker = SmartPicker(self.db)
        picked = picker.pick(400 * 1024)  # Pick ~400 KB
        
        # Step 2: Verify files were selected
        self.assertGreater(len(picked), 0)
        total_size = sum(os.stat(p).st_size for p in picked)
        self.assertLessEqual(total_size, 500 * 1024)  # Should be close to target
        
        # Step 3: Decrease priority
        original_prios = {}
        for path in picked:
            cursor = self.db.cursor
            cursor.execute("SELECT priority FROM details WHERE path=?", [path])
            original_prios[path] = cursor.fetchone()[0]
        
        picker.decrease_prio(picked)
        
        # Step 4: Verify priorities decreased
        self.db = Database(self.db_file.name)  # Reopen to see changes
        for path in picked:
            cursor = self.db.cursor
            cursor.execute("SELECT priority FROM details WHERE path=?", [path])
            new_prio = cursor.fetchone()[0]
            if original_prios[path] > 1:
                self.assertEqual(new_prio, original_prios[path] - 1)
        
        # Step 5: Copy to destination
        dest_dir = os.path.join(self.temp_dir, "destination")
        os.makedirs(dest_dir)
        picker.copy_list_to_destination(picked, dest_dir + os.sep)
        
        # Verify files were copied
        copied_files = os.listdir(dest_dir)
        self.assertEqual(len(copied_files), len(picked))
        for copied_file in copied_files:
            self.assertTrue(copied_file.startswith("000_") or copied_file.startswith("001_"))


if __name__ == "__main__":
    unittest.main()

