import unittest
import os
import tempfile
from morgy.song_cleankeeper.renamer import Renamer

class TestFunctionality(unittest.TestCase):
    def setUp(self):
        self.renamer = Renamer()

    def test_rename(self):
        temp_dir = tempfile.mkdtemp()
        old_file_1 = 'to_be_renamed1'
        old_file_2 = 'to_be_renamed2'
        new_file_1 = 'renamed_now1'
        new_file_2 = 'renamed_now2'

        recommendations_file_path = os.path.join(temp_dir, 'recommendations')
        with open(recommendations_file_path, 'w') as recommendations:
            recommendations.write('''{}
                {}\t{}
                {}\t{}
            '''.format(temp_dir, old_file_1, new_file_1, old_file_2, new_file_2))

        open(os.path.join(temp_dir, old_file_1), 'w').close()
        open(os.path.join(temp_dir, old_file_2), 'w').close()

        self.renamer.apply_recommendations(recommendations_file_path)

        self.assertFalse(os.path.exists(os.path.join(temp_dir, old_file_1)))
        self.assertFalse(os.path.exists(os.path.join(temp_dir, old_file_2)))
        self.assertTrue(os.path.exists(os.path.join(temp_dir, new_file_1)))
        self.assertTrue(os.path.exists(os.path.join(temp_dir, new_file_2)))


if __name__ == '__main__':
    unittest.main()
