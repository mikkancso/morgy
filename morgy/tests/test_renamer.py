import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from morgy.song_cleankeeper.renamer import Renamer


class TestFunctionality(unittest.TestCase):
    def setUp(self):
        # Suppress print statements during tests
        self.print_patcher = patch('builtins.print', MagicMock())
        self.print_patcher.start()
        
        self.renamer = Renamer()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        self.print_patcher.stop()
        shutil.rmtree(self.temp_dir)

    def test_rename(self):
        old_file_1 = "to_be_renamed1"
        old_file_2 = "to_be_renamed2"
        new_file_1 = "renamed_now1"
        new_file_2 = "renamed_now2"

        recommendations_file_path = os.path.join(self.temp_dir, "recommendations")
        with open(recommendations_file_path, "w") as recommendations:
            recommendations.write(
                """{}
                {}\t{}
                {}\t{}
            """.format(
                    self.temp_dir, old_file_1, new_file_1, old_file_2, new_file_2
                )
            )

        open(os.path.join(self.temp_dir, old_file_1), "w").close()
        open(os.path.join(self.temp_dir, old_file_2), "w").close()

        self.renamer.apply_recommendations(recommendations_file_path)

        self.assertFalse(os.path.exists(os.path.join(self.temp_dir, old_file_1)))
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir, old_file_2)))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, new_file_1)))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, new_file_2)))

    def test_rename_multiple_directories(self):
        dir1 = os.path.join(self.temp_dir, "dir1")
        dir2 = os.path.join(self.temp_dir, "dir2")
        os.makedirs(dir1)
        os.makedirs(dir2)

        old_file_1 = "file1.mp3"
        new_file_1 = "renamed1.mp3"
        old_file_2 = "file2.mp3"
        new_file_2 = "renamed2.mp3"

        with open(os.path.join(dir1, old_file_1), "w") as f:
            f.write("content1")
        with open(os.path.join(dir2, old_file_2), "w") as f:
            f.write("content2")

        recommendations_file_path = os.path.join(self.temp_dir, "recommendations")
        with open(recommendations_file_path, "w") as recommendations:
            recommendations.write(
                "{}\n{}\t{}\n{}\n{}\t{}\n".format(
                    dir1, old_file_1, new_file_1, dir2, old_file_2, new_file_2
                )
            )

        self.renamer.apply_recommendations(recommendations_file_path)

        self.assertTrue(os.path.exists(os.path.join(dir1, new_file_1)))
        self.assertTrue(os.path.exists(os.path.join(dir2, new_file_2)))
        self.assertFalse(os.path.exists(os.path.join(dir1, old_file_1)))
        self.assertFalse(os.path.exists(os.path.join(dir2, old_file_2)))


class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        # Suppress print statements during tests
        self.print_patcher = patch('builtins.print', MagicMock())
        self.print_patcher.start()
        
        self.renamer = Renamer()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        self.print_patcher.stop()
        shutil.rmtree(self.temp_dir)

    def test_file_not_found_error(self):
        """Test handling when source file doesn't exist."""
        recommendations_file_path = os.path.join(self.temp_dir, "recommendations")
        with open(recommendations_file_path, "w") as recommendations:
            recommendations.write(
                "{}\nnonexistent.mp3\trenamed.mp3\n".format(self.temp_dir)
            )

        # Should not raise exception, just print error
        try:
            self.renamer.apply_recommendations(recommendations_file_path)
        except Exception as e:
            self.fail("apply_recommendations raised {} unexpectedly".format(e))

    def test_malformed_input_missing_tab(self):
        """Test handling of malformed input without tab separator."""
        recommendations_file_path = os.path.join(self.temp_dir, "recommendations")
        with open(recommendations_file_path, "w") as recommendations:
            recommendations.write(
                "{}\nold_name.mp3 new_name.mp3\n".format(self.temp_dir)
            )

        # Should not raise exception, just skip the line
        try:
            self.renamer.apply_recommendations(recommendations_file_path)
        except Exception as e:
            self.fail("apply_recommendations raised {} unexpectedly".format(e))

    def test_malformed_input_multiple_tabs(self):
        """Test handling of input with multiple tabs."""
        old_file = "old.mp3"
        new_file = "new.mp3"
        with open(os.path.join(self.temp_dir, old_file), "w") as f:
            f.write("content")

        recommendations_file_path = os.path.join(self.temp_dir, "recommendations")
        with open(recommendations_file_path, "w") as recommendations:
            recommendations.write(
                "{}\n{}\t{}\textra_field\n".format(self.temp_dir, old_file, new_file)
            )

        # Renamer.split() will raise ValueError for multiple tabs
        # This is expected behavior - the renamer expects exactly one tab
        with self.assertRaises(ValueError):
            self.renamer.apply_recommendations(recommendations_file_path)

    def test_empty_recommendations_file(self):
        """Test handling of empty recommendations file."""
        recommendations_file_path = os.path.join(self.temp_dir, "recommendations")
        with open(recommendations_file_path, "w") as recommendations:
            recommendations.write("")

        # Should not raise exception
        try:
            self.renamer.apply_recommendations(recommendations_file_path)
        except Exception as e:
            self.fail("apply_recommendations raised {} unexpectedly".format(e))

    def test_recommendations_file_with_only_directory(self):
        """Test handling of file with only directory, no files."""
        recommendations_file_path = os.path.join(self.temp_dir, "recommendations")
        with open(recommendations_file_path, "w") as recommendations:
            recommendations.write("{}\n".format(self.temp_dir))

        # Should not raise exception
        try:
            self.renamer.apply_recommendations(recommendations_file_path)
        except Exception as e:
            self.fail("apply_recommendations raised {} unexpectedly".format(e))

    def test_whitespace_handling(self):
        """Test that whitespace is properly stripped."""
        old_file = "old.mp3"
        new_file = "new.mp3"
        with open(os.path.join(self.temp_dir, old_file), "w") as f:
            f.write("content")

        recommendations_file_path = os.path.join(self.temp_dir, "recommendations")
        with open(recommendations_file_path, "w") as recommendations:
            recommendations.write(
                "  {}\n  {}\t{}\n".format(self.temp_dir, old_file, new_file)
            )

        self.renamer.apply_recommendations(recommendations_file_path)

        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, new_file)))


if __name__ == "__main__":
    unittest.main()
