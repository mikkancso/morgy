import unittest
import os
from morgy.song_cleankeeper.path_sanitizer import PathSanitizer


class TestFunctionality(unittest.TestCase):
    def setUp(self):
        self.ps = PathSanitizer()

    def test_file_is_created(self):
        self.ps.write_recommendations(
            "/home/adatok/mp3Miki/01 Külföldi Punk/Bad Religion", "/tmp/test01"
        )
        self.assertTrue(os.path.isfile("/tmp/test01"))


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
