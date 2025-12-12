import unittest
import os
import shutil
import tempfile
from unittest.mock import patch

from click.testing import CliRunner

import morgy
from morgy.database import Database


class TestCLI(unittest.TestCase):
    """E2E tests for CLI commands."""
    
    def setUp(self):
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = tempfile.NamedTemporaryFile(delete=False)
        self.db_file.close()
        
        # Create a temporary database for testing
        self.test_db = Database(self.db_file.name)
        
        # Patch the db in morgy module
        self.original_db = morgy.db
        morgy.db = self.test_db
        
    def tearDown(self):
        # Restore original db
        morgy.db = self.original_db
        self.test_db.conn.close()
        os.unlink(self.db_file.name)
        shutil.rmtree(self.temp_dir)

    def test_update_command(self):
        """Test the update CLI command."""
        # Create test music directory
        music_dir = os.path.join(self.temp_dir, "music")
        artist_dir = os.path.join(music_dir, "Test Artist")
        album_dir = os.path.join(artist_dir, "1990 Album")
        os.makedirs(album_dir)
        
        with open(os.path.join(album_dir, "01 Song.mp3"), "w") as f:
            f.write("content")
        
        result = self.runner.invoke(morgy.morgy, ['update', music_dir])
        
        self.assertEqual(result.exit_code, 0)
        # Verify database was updated
        cursor = self.test_db.cursor
        cursor.execute("SELECT COUNT(*) FROM details")
        count = cursor.fetchone()[0]
        self.assertGreater(count, 0)

    def test_update_command_with_priority(self):
        """Test update command with custom priority."""
        music_dir = os.path.join(self.temp_dir, "music")
        artist_dir = os.path.join(music_dir, "Artist")
        album_dir = os.path.join(artist_dir, "1990 Album")
        os.makedirs(album_dir)
        
        with open(os.path.join(album_dir, "01 Song.mp3"), "w") as f:
            f.write("content")
        
        result = self.runner.invoke(morgy.morgy, ['update', '--priority', '5', music_dir])
        
        self.assertEqual(result.exit_code, 0)
        # Verify priority was set correctly
        cursor = self.test_db.cursor
        cursor.execute("SELECT priority FROM details")
        priorities = [row[0] for row in cursor.fetchall()]
        self.assertEqual(set(priorities), {5})

    def test_update_command_invalid_priority(self):
        """Test update command with invalid priority."""
        music_dir = os.path.join(self.temp_dir, "music")
        os.makedirs(music_dir)
        
        # Priority out of range
        result = self.runner.invoke(morgy.morgy, ['update', '--priority', '11', music_dir])
        self.assertNotEqual(result.exit_code, 0)
        
        # Priority too low
        result = self.runner.invoke(morgy.morgy, ['update', '--priority', '0', music_dir])
        self.assertNotEqual(result.exit_code, 0)

    def test_sanitize_command(self):
        """Test the sanitize CLI command."""
        # Create test directory with files to sanitize
        test_dir = os.path.join(self.temp_dir, "test")
        os.makedirs(test_dir)
        
        with open(os.path.join(test_dir, "01_TEST_SONG.mp3"), "w") as f:
            f.write("content")
        
        output_file = os.path.join(self.temp_dir, "recommendations.txt")
        result = self.runner.invoke(morgy.morgy, ['sanitize', test_dir, output_file])
        
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists(output_file))
        
        # Verify file has content
        with open(output_file, "r") as f:
            content = f.read()
            self.assertIn("01_TEST_SONG.mp3", content)

    def test_rename_command(self):
        """Test the rename CLI command."""
        test_dir = os.path.join(self.temp_dir, "test")
        os.makedirs(test_dir)
        
        old_file = os.path.join(test_dir, "old_name.mp3")
        new_file = os.path.join(test_dir, "new_name.mp3")
        with open(old_file, "w") as f:
            f.write("content")
        
        # Create recommendations file
        recommendations_file = os.path.join(self.temp_dir, "recommendations.txt")
        with open(recommendations_file, "w") as f:
            f.write("{}\n".format(test_dir))
            f.write("old_name.mp3\tnew_name.mp3\n")
        
        result = self.runner.invoke(morgy.morgy, ['rename', recommendations_file])
        
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(os.path.exists(old_file))
        self.assertTrue(os.path.exists(new_file))

    def test_mark_with_guitar_command(self):
        """Test the mark_with_guitar CLI command."""
        # Add a song to database first
        song_path = "/test/song.mp3"
        self.test_db.add_detail_row(song_path, "Artist", "1990", "Album", "1", "01", "Song", 1)
        
        result = self.runner.invoke(morgy.morgy, ['mark-with-guitar', song_path])
        
        self.assertEqual(result.exit_code, 0)
        # Verify guitar entry was added
        cursor = self.test_db.cursor
        cursor.execute("SELECT path FROM guitar WHERE path=?", [song_path])
        result_rows = cursor.fetchall()
        self.assertEqual(len(result_rows), 1)

    def test_write_playlist_command(self):
        """Test the write_playlist CLI command."""
        # Add songs to database
        song1 = "/test/song1.mp3"
        song2 = "/test/song2.mp3"
        self.test_db.add_detail_row(song1, "Artist1", "1990", "Album1", "1", "01", "Song1", 1)
        self.test_db.add_detail_row(song2, "Artist2", "1991", "Album2", "1", "02", "Song2", 1)
        
        playlist_file = os.path.join(self.temp_dir, "playlist.txt")
        result = self.runner.invoke(morgy.morgy, ['write-playlist', playlist_file, "artist='Artist1'"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists(playlist_file))
        
        # Verify playlist content
        with open(playlist_file, "r") as f:
            content = f.read()
            self.assertIn(song1, content)
            self.assertNotIn(song2, content)  # Should only have Artist1

    def test_pick_and_copy_command(self):
        """Test the pick_and_copy CLI command."""
        # Create test files
        source_dir = os.path.join(self.temp_dir, "source")
        os.makedirs(source_dir)
        
        file1 = os.path.join(source_dir, "song1.mp3")
        file2 = os.path.join(source_dir, "song2.mp3")
        with open(file1, "wb") as f:
            f.write(b"0" * (200 * 1024))  # 200 KB
        with open(file2, "wb") as f:
            f.write(b"0" * (300 * 1024))  # 300 KB
        
        # Add to database
        self.test_db.add_detail_row(file1, "Artist1", "1990", "Album1", "1", "01", "Song1", 1)
        self.test_db.add_detail_row(file2, "Artist2", "1991", "Album2", "1", "02", "Song2", 1)
        
        dest_dir = os.path.join(self.temp_dir, "dest")
        os.makedirs(dest_dir)
        
        result = self.runner.invoke(morgy.morgy, ['pick-and-copy', dest_dir, '1'])  # 1 MB
        
        self.assertEqual(result.exit_code, 0)
        # Verify files were copied
        copied_files = os.listdir(dest_dir)
        self.assertGreater(len(copied_files), 0)

    def test_write_guitar_files_command(self):
        """Test the write_guitar_files CLI command."""
        # Create test files
        source_dir = os.path.join(self.temp_dir, "source")
        os.makedirs(source_dir)
        
        file1 = os.path.join(source_dir, "guitar_song1.mp3")
        file2 = os.path.join(source_dir, "guitar_song2.mp3")
        with open(file1, "w") as f:
            f.write("content1")
        with open(file2, "w") as f:
            f.write("content2")
        
        # Add to database and mark as guitar
        self.test_db.add_detail_row(file1, "Artist1", "1990", "Album1", "1", "01", "Song1", 1)
        self.test_db.add_detail_row(file2, "Artist2", "1991", "Album2", "1", "02", "Song2", 1)
        self.test_db.add_guitar_row(file1, 1)
        self.test_db.add_guitar_row(file2, 1)
        
        dest_dir = os.path.join(self.temp_dir, "dest")
        os.makedirs(dest_dir)
        
        result = self.runner.invoke(morgy.morgy, ['write-guitar-files', dest_dir])
        
        self.assertEqual(result.exit_code, 0)
        # Verify files were copied
        copied_files = os.listdir(dest_dir)
        self.assertEqual(len(copied_files), 2)

    def test_integrate_command(self):
        """Test the integrate CLI command (with mocked user input)."""
        # Create integration source
        to_integrate = os.path.join(self.temp_dir, "to_integrate")
        leaf_dir = os.path.join(to_integrate, "Artist", "1990 Album")
        os.makedirs(leaf_dir)
        
        with open(os.path.join(leaf_dir, "01 Song.mp3"), "w") as f:
            f.write("content")
        
        dest_dir = os.path.join(self.temp_dir, "destination")
        os.makedirs(dest_dir)
        
        # Mock user input and vim
        with patch('builtins.input') as mock_input:
            with patch('os.system') as mock_system:
                def input_side_effect(prompt):
                    if "Destination folder" in prompt:
                        return dest_dir
                    return ""
                
                mock_input.side_effect = input_side_effect
                mock_system.return_value = None
                
                result = self.runner.invoke(morgy.morgy, ['integrate', to_integrate])
        
        # Should complete without error (though vim interaction is mocked)
        # The actual file moving and DB update would happen if not mocked
        self.assertIn(result.exit_code, [0])

    def test_cli_help(self):
        """Test that CLI help works."""
        result = self.runner.invoke(morgy.morgy, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Commands:", result.output)

    def test_command_help(self):
        """Test that individual command help works."""
        result = self.runner.invoke(morgy.morgy, ['update', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Update the database", result.output)


if __name__ == "__main__":
    unittest.main()

