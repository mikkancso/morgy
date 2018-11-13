import unittest
import os
import shutil
import tempfile

from morgy.smart_picker import SmartPicker
from morgy.database import Database


class TestSmartPicker(unittest.TestCase):
    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile()
        self.db = Database(self.db_file.name)
        self.smart_picker = SmartPicker(self.db)
        self._add_row_with_defaults()
        self._add_row_with_defaults(path="path2", prio="2")
        self._add_row_with_defaults(title="other title")
        # shutil.copyfile(Database.DEFAULT_PATH, self.db_file.name)

    def _add_row_with_defaults(
        self,
        path="path",
        artist="artist",
        year="1990",
        album="album",
        cd="1",
        number="01",
        title="title",
        prio="1",
    ):
        row_details = (path, artist, year, album, cd, number, title, prio)
        self.db.add_detail_row(*row_details)

    def test_build_dict_from_database(self):
        self.smart_picker.build_dict_from_database()
        # assert that dict is fine

    def test_get_weighted_selected_paths(self):
        titles = {
            "title": [("path", "1"), ("path2", "2")],
            "other title": [("path", "1")],
        }
        weighted_paths = self.smart_picker.get_weighted_selected_paths(titles)
        # assert


if __name__ == "__main__":
    unittest.main()
