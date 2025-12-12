import os
import tempfile
import unittest
from morgy.song_cleankeeper.path_sanitizer import PathSanitizer


class TestFunctionality(unittest.TestCase):
    def setUp(self):
        self.ps = PathSanitizer()
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "recommendations.txt")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_file_is_created(self):
        # Create a test directory with a file
        test_subdir = os.path.join(self.temp_dir, "test_subdir")
        os.makedirs(test_subdir)
        with open(os.path.join(test_subdir, "song.mp3"), "w") as f:
            f.write("fake content")
        
        self.ps.write_recommendations(self.temp_dir, self.output_file)
        self.assertTrue(os.path.isfile(self.output_file))

    def test_write_recommendations_content_format(self):
        test_subdir = os.path.join(self.temp_dir, "test_subdir")
        os.makedirs(test_subdir)
        with open(os.path.join(test_subdir, "01_test_song.mp3"), "w") as f:
            f.write("fake content")
        
        self.ps.write_recommendations(self.temp_dir, self.output_file)
        
        with open(self.output_file, "r") as f:
            content = f.read()
        
        # Should contain directory path and file recommendation
        self.assertIn(test_subdir, content)
        self.assertIn("01_test_song.mp3", content)
        self.assertIn("\t", content)  # Tab separator

    def test_recommendation_generator_single_file(self):
        test_subdir = os.path.join(self.temp_dir, "test_subdir")
        os.makedirs(test_subdir)
        with open(os.path.join(test_subdir, "song.mp3"), "w") as f:
            f.write("fake content")
        
        recommendations = list(self.ps.recommendation_generator(self.temp_dir))
        
        # Should have directory line + file recommendation line
        self.assertGreaterEqual(len(recommendations), 2)
        self.assertEqual(recommendations[0].strip(), test_subdir)
        self.assertIn("song.mp3", recommendations[1])

    def test_recommendation_generator_multiple_files(self):
        test_subdir = os.path.join(self.temp_dir, "test_subdir")
        os.makedirs(test_subdir)
        with open(os.path.join(test_subdir, "01_song_one.mp3"), "w") as f:
            f.write("fake")
        with open(os.path.join(test_subdir, "02_song_two.mp3"), "w") as f:
            f.write("fake")
        
        recommendations = list(self.ps.recommendation_generator(self.temp_dir))
        
        # Should process multiple files
        file_lines = [r for r in recommendations if "\t" in r]
        self.assertEqual(len(file_lines), 2)

    def test_recommendation_generator_filters_extensions(self):
        test_subdir = os.path.join(self.temp_dir, "test_subdir")
        os.makedirs(test_subdir)
        with open(os.path.join(test_subdir, "song.mp3"), "w") as f:
            f.write("fake")
        with open(os.path.join(test_subdir, "song.wma"), "w") as f:
            f.write("fake")
        with open(os.path.join(test_subdir, "song.flac"), "w") as f:
            f.write("fake")
        with open(os.path.join(test_subdir, "song.txt"), "w") as f:
            f.write("fake")
        
        recommendations = list(self.ps.recommendation_generator(self.temp_dir))
        
        file_lines = [r for r in recommendations if "\t" in r]
        self.assertEqual(len(file_lines), 3)  # mp3, wma, flac only

    def test_recommendation_generator_case_insensitive_extensions(self):
        test_subdir = os.path.join(self.temp_dir, "test_subdir")
        os.makedirs(test_subdir)
        with open(os.path.join(test_subdir, "song.MP3"), "w") as f:
            f.write("fake")
        with open(os.path.join(test_subdir, "song.WMA"), "w") as f:
            f.write("fake")
        
        recommendations = list(self.ps.recommendation_generator(self.temp_dir))
        
        file_lines = [r for r in recommendations if "\t" in r]
        self.assertEqual(len(file_lines), 2)

    def test_recommendation_generator_empty_directory(self):
        test_subdir = os.path.join(self.temp_dir, "test_subdir")
        os.makedirs(test_subdir)
        
        recommendations = list(self.ps.recommendation_generator(self.temp_dir))
        
        # Should only have directory line, no file recommendations
        file_lines = [r for r in recommendations if "\t" in r]
        self.assertEqual(len(file_lines), 0)

    def test_recommendation_generator_nested_directories(self):
        level1 = os.path.join(self.temp_dir, "level1")
        level2 = os.path.join(level1, "level2")
        os.makedirs(level2)
        
        with open(os.path.join(level2, "song.mp3"), "w") as f:
            f.write("fake")
        
        recommendations = list(self.ps.recommendation_generator(self.temp_dir))
        
        # Should have recommendations from nested directory
        file_lines = [r for r in recommendations if "\t" in r]
        self.assertEqual(len(file_lines), 1)

    def test_process_integration(self):
        filelist = [
            "01_artist_song_one.mp3",
            "02_artist_song_two.mp3",
            "03_artist_song_three.mp3",
        ]
        
        result = self.ps.process(filelist)
        
        self.assertEqual(len(result), 3)
        self.assertTrue(all(f.endswith(".mp3") for f in result))

    def test_preprocess_integration(self):
        filename = "01_THE_SONG-NAME.mp3"
        result = self.ps.preprocess(filename)
        
        # Should lowercase, remove dashes/underscores, correct spaces
        self.assertNotIn("_", result)
        self.assertNotIn("-", result)
        self.assertIn("01", result)

    def test_postprocess_integration(self):
        filename = "01 test song.mp3"
        result = self.ps.postprocess(filename)
        
        # Should capitalize first letter after number
        self.assertIn("Test", result)

    def test_full_workflow_single_file(self):
        test_subdir = os.path.join(self.temp_dir, "test_subdir")
        os.makedirs(test_subdir)
        with open(os.path.join(test_subdir, "01_TEST_SONG-NAME.mp3"), "w") as f:
            f.write("fake")
        
        self.ps.write_recommendations(self.temp_dir, self.output_file)
        
        with open(self.output_file, "r") as f:
            content = f.read()
        
        # Should have processed the filename
        self.assertIn("01_TEST_SONG-NAME.mp3", content)  # Original
        # Processed version should be different (lowercase, no dashes/underscores)
        lines = content.split("\n")
        for line in lines:
            if "\t" in line:
                original, processed = line.split("\t")
                self.assertNotEqual(original, processed.strip())


class TestHelperFunctions(unittest.TestCase):
    def setUp(self):
        self.ps = PathSanitizer()

    @unittest.skip("feature request")
    def test_upper_first_and_all_before_dot(self):
        self.assertEqual(
            self.ps.upper_first_and_all_after_dot(
                "42 i dont want to be a member of a.b.c. anymore.mp3"
            ),
            "42 I dont want to be a member of A.B.C. anymore.mp3",
        )

    @unittest.skip("feature request")
    def test_upper_all_after_dot(self):
        self.assertEqual(
            self.ps.upper_first_and_all_after_dot("42 mr. clean.mp3"),
            "42 Mr. Clean.mp3",
        )

    def test_dashes_are_removed(self):
        self.assertTrue(
            "-"
            not in self.ps.handle_dash_and_underscore(
                "04._The_Doors_-_The_Soft_Parade_-_Do_It.mp3"
            )
        )

    def test_underscores_are_removed(self):
        self.assertTrue(
            "_"
            not in self.ps.handle_dash_and_underscore(
                "04._The_Doors_-_The_Soft_Parade_-_Do_It.mp3"
            )
        )

    def test_correct_spaces_if_does_not_start_with_digits(self):
        self.assertEqual(
            self.ps.correct_spaces("The  hey-a-ho   cookoo  .mp3"),
            "The hey-a-ho cookoo.mp3",
        )

    def test_correct_spaces_if_no_space_follows_digits(self):
        self.assertEqual(
            self.ps.correct_spaces("02The  hey-a-ho   cookoo  .mp3"),
            "02 The hey-a-ho cookoo.mp3",
        )

    def test_correct_spaces_if_dot_follows_digits(self):
        self.assertEqual(
            self.ps.correct_spaces("02.The  hey-a-ho   cookoo  .mp3"),
            "02 The hey-a-ho cookoo.mp3",
        )

    def test_correct_spaces_if_dot_and_space_follows_digits(self):
        self.assertEqual(
            self.ps.correct_spaces("02. The  hey-a-ho   cookoo  .mp3"),
            "02 The hey-a-ho cookoo.mp3",
        )

    def test_delete_matches_forward_and_backward(self):
        self.assertEqual(
            self.ps.delete_matches(
                [
                    "a B c d E fpo".split(),
                    "g B c z E f".split(),
                    "h B ce z f E tf".split(),
                ]
            ),
            ["a c d fpo".split(), "g c z f".split(), "h ce z f tf".split()],
        )

    def test_delete_matches_multiple_matches(self):
        self.assertEqual(
            self.ps.delete_matches(
                [
                    "a B C d W 5 E fpo GR TL 2".split(),
                    "g B C z W 4 3 E f GR TL 43".split(),
                    "h B C z W 3 6 8f E tf GR TL 1".split(),
                ]
            ),
            ["a d 5 fpo 2".split(), "g z 4 3 f 43".split(), "h z 3 6 8f tf 1".split()],
        )

    def test_delete_matches_no_matches(self):
        self.assertEqual(
            self.ps.delete_matches(
                ["a c d fpo".split(), "g c z f".split(), "h ce z f tf".split()]
            ),
            ["a c d fpo".split(), "g c z f".split(), "h ce z f tf".split()],
        )

    def test_delete_matches_crossing_matches(self):
        self.assertEqual(
            self.ps.delete_matches(
                [
                    "a B c d E fpo".split(),
                    "g c B z E f q".split(),
                    "h ce z B E tf q qq".split(),
                ]
            ),
            ["a c d fpo".split(), "g c z f q".split(), "h ce z tf q qq".split()],
        )

    def test_delete_matches_with_last_match(self):
        self.assertEqual(
            self.ps.delete_matches(
                [
                    "a B c d E fpo last".split(),
                    "g B c z E f last".split(),
                    "h B ce z f E tf last".split(),
                ]
            ),
            ["a c d fpo".split(), "g c z f".split(), "h ce z f tf".split()],
        )


if __name__ == "__main__":
    unittest.main()
